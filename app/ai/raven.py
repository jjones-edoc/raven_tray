from typing import List, Dict, Any

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from tools.file_operations import read_prompt_from_file, extract_function_call, clean_string
from tools.logging_utils import log_ai_interaction, logger
from .memory import save_data, search_data, delete_data
from .onlinesearch import perplexity_search

model = ChatOpenAI(model="gpt-4o")


def get_message_placeholder(messages: List[Dict[str, Any]]) -> List[Any]:
    message_history = []
    for message in messages:
        if message['role'] == 'human':
            message_history.append(HumanMessage(message['content']))
        elif message['role'] == 'ai':
            message_history.append(AIMessage(message['content']))
    return message_history


def online_search(query: str) -> str:
    online_results = perplexity_search(query)
    character_prompt = read_prompt_from_file('character.md')
    online_prompt = read_prompt_from_file('onlinesearch.md')
    full_prompt = f"{character_prompt}\n\n{online_prompt}"
    full_prompt = full_prompt.replace('{user_prompt}', query)
    full_prompt = full_prompt.replace('{online_results}', online_results)
    response = model.invoke([HumanMessage(content=full_prompt)])
    return response.content


def respond(query: str) -> str:
    return clean_string(query)


@log_ai_interaction
def execute_command(command: str, inquiry: str) -> str:
    function_map = {
        "searchdata": search_data,
        "savedata": save_data,
        "deletedata": delete_data,
        "onlinesearch": online_search,
        "respond": respond,
    }

    if command in function_map:
        logger.info(f"Executing function {command}({inquiry})")
        return function_map[command](inquiry)
    else:
        logger.warning(f"Function {command} not recognized.")
        return f"Error: Function {command} not recognized."


@log_ai_interaction
def general_chat_raven(messages: List[Dict[str, Any]]) -> str:
    character_prompt = read_prompt_from_file('character.md')
    functions_prompt = read_prompt_from_file('functions.md')

    formatted_messages = get_message_placeholder(messages)

    full_prompt = f"{character_prompt}\n\n{functions_prompt}"

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=full_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    chain = prompt | model

    response = chain.invoke({"messages": formatted_messages})
    ai_response = response.content
    logger.info(f"Initial response: {ai_response}")

    function_name, arguments = extract_function_call(ai_response)

    if function_name is None:
        return ai_response

    logger.info(f"Function name: {function_name}")
    logger.info(f"Arguments: {arguments}")

    if function_name:
        ai_response = execute_command(function_name, arguments)

    return ai_response
