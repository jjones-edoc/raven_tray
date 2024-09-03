from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.chat_history import HumanMessage, AIMessage
from tools.file_operations import read_prompt_from_file

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

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                system_prompt,
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    formatted_messages = get_message_placeholder(messages)

    print(formatted_messages)

    chain = prompt | model

    response = chain.invoke({"messages": formatted_messages})

    return response.content
