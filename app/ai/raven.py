import json
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from tools.file_operations import read_prompt_from_file
from .memory import insert_document, search_similarity, delete_documents_by_query
from .tools import process_tools_command

model = ChatOpenAI(model="gpt-4o")


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
    # memory_prompt = read_prompt_from_file('memory.md')

    formatted_messages = get_message_placeholder(messages)

    full_prompt = system_prompt

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=full_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    chain = prompt | model

    response = chain.invoke({"messages": formatted_messages})
    ai_response = response.content

    # if the response starts with TOOLS then call the tools function
    if ai_response.startswith('TOOLS'):
        ai_response = process_tools_command(ai_response)

    return ai_response
