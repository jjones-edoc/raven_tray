from typing import List, Dict, Any
from datetime import date

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from tools.file_operations import read_prompt_from_file, extract_function_calls, clean_string
from tools.logging_utils import logger
from .memory import save_data, search_data, delete_data
from .onlinesearch import perplexity_search
from app.db import db_query, db_command

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


def run_query(query) -> str:
    return db_query(query)


def run_command(command_str) -> str:
    return db_command(command_str)


def respond(query: str) -> str:
    return clean_string(query)


def execute_command(command: str, inquiry=()) -> str:
    function_map = {
        "searchdata": search_data,
        "savedata": save_data,
        "deletedata": delete_data,
        "onlinesearch": online_search,
        "query": run_query,
        "command": run_command,
        "respond": respond,
    }

    try:

        if command in function_map:
            logger.debug(f"Executing function: {command}")
            return function_map[command](inquiry)
        else:
            logger.warning(f"Function {command} not recognized.")
            return f"Error: Function {command} not recognized."
    except Exception as e:
        logger.error(f"Error executing function {command}: {e}")
        return f"exception: {e}"


def general_chat_raven(messages: List[Dict[str, Any]]) -> str:
    logger.info(f"AI Interaction - Input: {messages}")

    character_prompt = read_prompt_from_file('character.md')
    functions_prompt = read_prompt_from_file('functions.md')
    functions_prompt = functions_prompt.replace(
        '{DATE}', date.today().strftime('%Y-%m-%d'))

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
    logger.info(f"Initial AI response: {ai_response}")

    function_calls = extract_function_calls(ai_response)
    # only do the first function call
    if len(function_calls) == 0:
        logger.info(f"AI Interaction - Output: {ai_response}")
        return ai_response

    function_name, arguments = function_calls[0]
    if function_name is None:
        logger.info(f"AI Interaction - Output: {ai_response}")
        return ai_response

    logger.info(f"Extracted function: {function_name}({arguments})")

    if function_name:
        result = execute_command(function_name, arguments)
        logger.info(f"Function {function_name} result: {result}")
        ai_response = result

    logger.info(f"AI Interaction - Output: {ai_response}")
    return ai_response


def task_talk(user_msg, tasks_info) -> str:
    logger.info(f"AI Interaction - Input: {user_msg}")
    character_prompt = read_prompt_from_file('character.md')
    tasks_prompt = read_prompt_from_file('tasks.md')
    example_tasks_prompt = read_prompt_from_file('example_tasks.md')
    tasks_prompt = tasks_prompt.replace(
        '{date}', date.today().strftime('%Y-%m-%d'))
    tasks_prompt = tasks_prompt.replace('{user_prompt}', user_msg)
    tasks_prompt = tasks_prompt.replace('{tasks_info}', tasks_info)
    previous_actions = ""
    count = 0
    while count < 4:  # Limiting the number of allowed actions to prevent infinite loops
        prv_prompt = ""
        if previous_actions != "":
            prv_prompt = f"###Functions already called\n\n{previous_actions}"
        else:
            prv_prompt = example_tasks_prompt
        full_prompt = f"{character_prompt}\n\n{
            tasks_prompt.replace('{previous_actions}', prv_prompt)}"
        logger.info(f"Full prompt: {full_prompt}")
        response = model.invoke([HumanMessage(content=full_prompt)])
        ai_response = response.content
        logger.info(f"AI task response: {ai_response}")

        function_calls = extract_function_calls(ai_response)
        for function_name, arguments in function_calls:
            if function_name is None:
                continue
            logger.info(f"Extracted function: {function_name}({arguments})")
            previous_actions += f"Function call:\n\n{
                function_name}({arguments})\n\n"
            result = execute_command(function_name, arguments)
            logger.info(f"Function {function_name} result: {result}")
            if function_name == "respond":
                return result
            previous_actions += f"Result of function:\n\n{result}\n\n"
        count += 1
    return "I'm sorry, I'm unable to help with that at the moment."
