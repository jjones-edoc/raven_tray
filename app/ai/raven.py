from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.chat_history import HumanMessage, AIMessage
from tools.file_operations import read_prompt_from_file
from .memory import store_memory, retrieve_memory, delete_memory

model = ChatOpenAI(model="gpt-3.5-turbo")


def get_message_placeholder(messages: list[dict[str, any]]):
    message_history = []
    for message in messages:
        if message['role'] == 'human':
            message_history.append(HumanMessage(message['content']))
        elif message['role'] == 'ai':
            message_history.append(AIMessage(message['content']))
    return message_history


def general_chat_raven(messages: list[dict[str, any]]):
    system_prompt = read_prompt_from_file('raven.md')
    memory_prompt = read_prompt_from_file('memory.md')

    formatted_messages = get_message_placeholder(messages)

    # Check if the last message contains memory-related keywords
    memory_keywords = ['remember', 'recall', 'forget', 'memory']
    last_message = formatted_messages[-1].content.lower() if formatted_messages else ""
    use_memory_prompt = any(keyword in last_message for keyword in memory_keywords)

    if use_memory_prompt:
        full_prompt = system_prompt + "\n\n" + memory_prompt
    else:
        full_prompt = system_prompt

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                full_prompt,
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    chain = prompt | model

    # Check for specific memory operations
    if "remember" in last_message:
        # Extract the information to remember (this is a simple example, you might need more sophisticated parsing)
        info_to_remember = last_message.split("remember", 1)[1].strip()
        store_memory("user_info", info_to_remember)
    elif "do you recall" in last_message or "do you remember" in last_message:
        # Perform a memory retrieval
        retrieved_info = retrieve_memory(last_message)
        if retrieved_info:
            formatted_messages.append(AIMessage(f"I recall this information: {retrieved_info}"))
    elif "forget" in last_message:
        # Perform a memory deletion
        if delete_memory(last_message):
            formatted_messages.append(AIMessage("I've forgotten that information."))
        else:
            formatted_messages.append(AIMessage("I couldn't find that specific information to forget."))

    response = chain.invoke({"messages": formatted_messages})

    return response.content
