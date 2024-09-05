from tools.file_operations import read_prompt_from_file
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from .memory import insert_document, search_similarity, search_max_rel, delete_documents_by_query
from langchain_core.documents import Document

model = ChatOpenAI(model="gpt-4o")


def process_searched_documents(inquery: str, documents: list[Document]):
    if not documents:
        return "I wasn't able to recall the information you requested."

    content = ""
    for i, doc in enumerate(documents):
        content += f"Document {i + 1}:\n"
        content += f"ID: {doc.metadata['id']}\n"
        content += f"Content: {doc.page_content}\n\n"

    memory_prompt = read_prompt_from_file('memory.md')

    # replace tools_prompt {user_prompt} with the command
    full_prompt = memory_prompt.replace('{user_prompt}', inquery)
    full_prompt = full_prompt.replace('{documents}', content)

    response = model.invoke([HumanMessage(content=full_prompt)])

    return response.content


def execute_command(command, inquiry: str):
    command = command.strip().lower()

    if command.startswith("insert_memory"):
        data = command[len("insert_memory"):].strip()
        print('calling insert_document with data:', data)
        stored_id = insert_document(data)
        return f"Document stored with id: {stored_id}"

    elif command.startswith("search_memory"):
        query = command[len("search_memory"):].strip()
        print('calling search_similarity with query:', query)
        docs = search_similarity(query)
        return process_searched_documents(inquiry, docs)

    elif command.startswith("search_memory_max_rel"):
        query = command[len("search_memory_max_rel"):].strip()
        print('calling search_max_rel with query:', query)
        docs = search_max_rel(query)
        return process_searched_documents(inquiry, docs)

    elif command.startswith("delete_memory"):
        query = command[len("delete_memory"):].strip()
        print('calling delete_documents_by_query with query:', query)
        deleted = delete_documents_by_query(query)
        return f"Deleted {deleted} documents"

    else:
        return "I messed something up and was unable to complete your request."


def process_tools_command(ai_response: str):
    # extract the command from the response by removing TOOLS
    command = ai_response[6:]
    # continue deleting until you hit the first alphanumeric character ignore - or whitespace
    while not command[0].isalnum():
        command = command[1:]

    tools_prompt = read_prompt_from_file('tools.md')

    # replace tools_prompt {user_prompt} with the command
    full_prompt = tools_prompt.replace('{user_prompt}', command)

    response = model.invoke([HumanMessage(content=full_prompt)])

    return execute_command(response.content, command)
