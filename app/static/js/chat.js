const initializeChat = (messages, channelId) => {
  $(document).ready(() => {
    const socket = io();
    const chatArea = $("#chat-area");

    socket.emit("join", { channel_id: channelId });

    const appendMessageToChat = (type, content) => {
      const sanitizedContent = DOMPurify.sanitize(marked.parse(content));
      chatArea.append(`<div class="message ${type}">${sanitizedContent}</div>`);
      // Scroll to the bottom after appending new message
      chatArea.scrollTop(chatArea[0].scrollHeight);
    };

    socket.on("receive_message", ({ type, ai_message, user_message, error_message }) => {
      switch (type) {
        case "reset":
          chatArea.empty();
          appendMessageToChat("ai", "Thank you, how can I help you?");
          break;
        case "response":
          appendMessageToChat("ai", ai_message.content);
          break;
        case "message":
          appendMessageToChat("human", user_message.content);
          break;
        case "error":
          appendMessageToChat("ai", error_message.content);
          break;
        case "clear":
          chatArea.empty();
          break;
        default:
          console.log("Unrecognized type", type);
      }
    });

    const sendMessage = () => {
      const messageInput = document.getElementById("message-input");
      const messageContent = messageInput.value;

      if (!messageContent) {
        return;
      }

      socket.emit("send_message", { channel_id: channelId, message_content: messageContent });

      messageInput.value = "";
    };

    document.getElementById("submit-button").addEventListener("click", sendMessage);

    messages.forEach(({ role, content }) => {
      const className = role === "ai" ? "ai" : "human";
      appendMessageToChat(className, content);
    });

    chatArea.scrollTop(chatArea[0].scrollHeight);

    $("#message-input").keydown((event) => {
      if (event.keyCode === 13 && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
      }
    });
  });
};
