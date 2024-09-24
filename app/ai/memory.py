import uuid
from typing import List, Optional

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage

from tools.file_operations import read_prompt_from_file
from tools.logging_utils import logger

# Constants
PERSIST_DIRECTORY = 'chroma_db'
MODEL_NAME = "gpt-4o"

# Initialize OpenAI embeddings
embeddings = OpenAIEmbeddings()

# Initialize Chroma vector store
vectorstore = Chroma(persist_directory=PERSIST_DIRECTORY,
                     embedding_function=embeddings)

model = ChatOpenAI(model=MODEL_NAME)


def process_searched_documents(inquery: str, documents: List[Document]) -> str:
    """Process searched documents and generate a response."""
    logger.info(f"Processing {len(documents)} documents for query: {inquery}")
    if not documents:
        return "I wasn't able to recall the information you requested."

    content = format_documents(documents)
    full_prompt = create_full_prompt(inquery, content)

    try:
        response = model.invoke([HumanMessage(content=full_prompt)])
        logger.debug(f"AI response: {response.content}")
        return response.content
    except Exception as e:
        logger.error(f"Error in processing documents: {e}")
        return "An error occurred while processing your request."


def format_documents(documents: List[Document]) -> str:
    """Format the documents into a string."""
    return "\n\n".join(
        f"Document {
            i + 1}:\nID: {doc.metadata['id']}\nContent: {doc.page_content}"
        for i, doc in enumerate(documents)
    )


def create_full_prompt(inquery: str, content: str) -> str:
    """Create the full prompt for the AI model."""
    character_prompt = read_prompt_from_file('character.md')
    memory_prompt = read_prompt_from_file('memory.md')
    full_prompt = f"{character_prompt}\n\n{memory_prompt}"
    return full_prompt.replace('{user_prompt}', inquery).replace('{documents}', content)


def insert_document(data: str) -> str:
    """Insert a new document into the vector store."""
    doc_id = str(uuid.uuid4())
    try:
        vectorstore.add_documents(
            documents=[Document(page_content=data, metadata={"id": doc_id})], ids=[doc_id]
        )
        logger.info(f"Inserted document with ID: {doc_id}")
        return doc_id
    except Exception as e:
        logger.error(f"Error inserting document: {e}")
        return ""


def delete_data(query: str) -> str:
    """Delete data based on a query."""
    try:
        # Search for relevant documents
        docs = search_similarity(query)
        logger.info(f"Found {len(docs)} potential documents to delete.")

        # Create the delete prompt with the found documents
        full_prompt = create_delete_prompt(query, docs)

        # Get AI's response (list of IDs to delete)
        response = model.invoke([HumanMessage(content=full_prompt)])

        # Parse the response to get the list of IDs
        ids_to_delete = [id.strip()
                         for id in response.content.split(',') if id.strip()]

        logger.info(f"Deleting {len(ids_to_delete)} documents.")

        # Delete the specified documents
        deleted_count = delete_documents_by_ids(ids_to_delete)

        # Create a response about the deletion
        result_prompt = create_delete_result_prompt(query, deleted_count)
        final_response = model.invoke([HumanMessage(content=result_prompt)])
        logger.info(f"Final response: {final_response.content}")

        return final_response.content
    except Exception as e:
        logger.error(f"Error in delete_data: {e}")
        return "An error occurred while deleting data."


def save_data(query: str) -> str:
    """Save data and generate a response."""
    try:
        res = insert_document(query)
        full_prompt = create_save_prompt(query, res)
        response = model.invoke([HumanMessage(content=full_prompt)])
        logger.debug(f"AI response: {response.content}")
        return response.content
    except Exception as e:
        logger.error(f"Error in save_data: {e}")
        return "An error occurred while saving data."


def search_data(query: str) -> str:
    """Search data based on a query."""
    return process_searched_documents(query, search_similarity(query))


def search_similarity(query: str, k: int = 3) -> List[Document]:
    """Perform a similarity search."""
    return vectorstore.similarity_search(query, k)


def search_similarity_threshold(query: str, k: int = 3, threshold: float = 0.5) -> List[Document]:
    """Perform a similarity search with a threshold."""
    return vectorstore.search(query, search_type="similarity_score_threshold", k=k, score_threshold=threshold)


def search_max_rel(query: str, k: int = 3) -> List[Document]:
    """Perform a max marginal relevance search."""
    return vectorstore.max_marginal_relevance_search(query, k)


def delete_documents_by_query(query: str, threshold: float = 0.1) -> int:
    """Delete documents based on a query."""
    k = 100
    total_deleted = 0
    try:
        while True:
            logger.info(f"Searching for documents to delete with threshold {
                        threshold}...")
            docs = search_similarity_threshold(query, k=k, threshold=threshold)
            document_ids = [result.metadata["id"] for result in docs]

            if document_ids:
                vectorstore.delete(ids=document_ids)
                total_deleted += len(document_ids)
                logger.info(f"Deleted {len(document_ids)} documents.")

            if len(document_ids) < k:
                break
    except Exception as e:
        logger.error(f"An error occurred during document deletion: {e}")
    return total_deleted


def delete_documents_by_ids(ids: List[str]) -> int:
    """Delete documents by their IDs."""
    try:
        logger.debug(f"Deleting documents by IDs: {ids}")
        vectorstore.delete(ids=ids)
        return len(ids)
    except Exception as e:
        logger.error(f"Error deleting documents by IDs: {e}")
        return 0


def create_delete_prompt(query: str, documents: List[Document]) -> str:
    """Create the prompt for delete operation."""
    character_prompt = read_prompt_from_file('character.md')
    delete_prompt = read_prompt_from_file('deletememory.md')
    formatted_docs = format_documents(documents)
    return f"{character_prompt}\n\n{delete_prompt}".replace('{query}', query).replace('{documents}', formatted_docs)


def create_delete_result_prompt(query: str, deleted_count: int) -> str:
    """Create the prompt for delete result."""
    character_prompt = read_prompt_from_file('character.md')
    delete_result_prompt = read_prompt_from_file('deletememory_result.md')
    return f"{character_prompt}\n\n{delete_result_prompt}".replace('{query}', query).replace('{deleted_count}', str(deleted_count))


def create_save_prompt(query: str, result: str) -> str:
    """Create the prompt for save operation."""
    character_prompt = read_prompt_from_file('character.md')
    save_prompt = read_prompt_from_file('savememory.md')
    return f"{character_prompt}\n\n{save_prompt}".replace('{save_data}', query).replace('{save_result}', result)
