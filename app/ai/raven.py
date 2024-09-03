import json
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

    formatted_messages = get_message_placeholder(messages)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                system_prompt,
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    chain = prompt | model

    response = chain.invoke({"messages": formatted_messages})
    ai_response = response.content

    # Check for memory operations in the AI response
    memory_operation = None
    try:
        # Extract the JSON part from the response
        json_start = ai_response.rfind('{"operation":')
        if json_start != -1:
            json_str = ai_response[json_start:]
            memory_operation = json.loads(json_str)
            # Remove the JSON part from the response
            ai_response = ai_response[:json_start].strip()
    except json.JSONDecodeError:
        pass

    if memory_operation:
        if memory_operation['operation'] == 'store':
            store_memory(memory_operation['key'], memory_operation['value'])
        elif memory_operation['operation'] == 'retrieve':
            retrieved_info = retrieve_memory(memory_operation['query'])
            if retrieved_info:
                ai_response += f"\n\nI recall this information: {retrieved_info}"
            else:
                ai_response += "\n\nI'm sorry, but I don't have any information stored about that topic."
        elif memory_operation['operation'] == 'delete':
            if delete_memory(memory_operation['query']):
                ai_response += "\n\nI've forgotten that information."
            else:
                ai_response += "\n\nI couldn't find that specific information to forget."

    return ai_response
