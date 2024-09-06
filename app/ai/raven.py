from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from tools.file_operations import read_prompt_from_file, extract_function_call, clean_string
from .memory import save_data, search_data, delete_data


model = ChatOpenAI(model="gpt-4o")


def get_message_placeholder(messages: list[dict[str, any]]):
    message_history = []
    for message in messages:
        if message['role'] == 'human':
            message_history.append(HumanMessage(message['content']))
        elif message['role'] == 'ai':
            message_history.append(AIMessage(message['content']))
    return message_history


def online_search(query: str):
    # This function should be implemented to search the web for the query
    return "I'm sorry, I'm not able to search the web at this time."


def respond(query: str):
    return clean_string(query)


def execute_command(command, inquiry: str):
    function_map = {
        "searchdata": search_data,
        "savedata": save_data,
        "deletedata": delete_data,
        "onlinesearch": online_search,
        "respond": respond,
    }

    if command in function_map:
        print(f"Executing function {command}({inquiry})")
        return function_map[command](inquiry)
    else:
        print(f"Function {command} not recognized.")


def general_chat_raven(messages: list[dict[str, any]]):
    character_prompt = read_prompt_from_file('character.md')
    functions_prompt = read_prompt_from_file('functions.md')

    formatted_messages = get_message_placeholder(messages)

    full_prompt = character_prompt + "\n\n" + functions_prompt

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=full_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    chain = prompt | model

    response = chain.invoke({"messages": formatted_messages})
    ai_response = response.content
    print("Initial response: "+ai_response)
    function_name, arguments = extract_function_call(ai_response)

    if function_name == None:
        return ai_response

    print("Function name: "+function_name)
    print("Arguments: "+arguments)
    if function_name:
        ai_response = execute_command(function_name, arguments)

    return ai_response
