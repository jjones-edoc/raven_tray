import uuid
from typing import List, Optional

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage

from tools.file_operations import read_prompt_from_file

# Constants
PERSIST_DIRECTORY = 'chroma_db'
MODEL_NAME = "gpt-4o"

# Initialize OpenAI embeddings
embeddings = OpenAIEmbeddings()

# Initialize Chroma vector store
vectorstore = Chroma(persist_directory=PERSIST_DIRECTORY, embedding_function=embeddings)

model = ChatOpenAI(model=MODEL_NAME)

def process_searched_documents(inquery: str, documents: List[Document]) -> str:
    """Process searched documents and generate a response."""
    print(f"Processing {len(documents)} documents for query: {inquery}")
    if not documents:
        return "I wasn't able to recall the information you requested."
    
    content = format_documents(documents)
    full_prompt = create_full_prompt(inquery, content)
    
    try:
        response = model.invoke([HumanMessage(content=full_prompt)])
        return response.content
    except Exception as e:
        print(f"Error in processing documents: {e}")
        return "An error occurred while processing your request."

def format_documents(documents: List[Document]) -> str:
    """Format the documents into a string."""
    return "\n\n".join(
        f"Document {i + 1}:\nID: {doc.metadata['id']}\nContent: {doc.page_content}"
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
        return doc_id
    except Exception as e:
        print(f"Error inserting document: {e}")
        return ""

def delete_data(query: str) -> str:
    """Delete data based on a query."""
    try:
        res = delete_documents_by_query(query)
        full_prompt = create_delete_prompt(query, str(res))
        response = model.invoke([HumanMessage(content=full_prompt)])
        return response.content
    except Exception as e:
        print(f"Error in delete_data: {e}")
        return "An error occurred while deleting data."

def save_data(query: str) -> str:
    """Save data and generate a response."""
    try:
        res = insert_document(query)
        full_prompt = create_save_prompt(query, res)
        response = model.invoke([HumanMessage(content=full_prompt)])
        return response.content
    except Exception as e:
        print(f"Error in save_data: {e}")
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
            docs = search_similarity_threshold(query, k=k, threshold=threshold)
            document_ids = [result.metadata["id"] for result in docs]

            if document_ids:
                vectorstore.delete(ids=document_ids)
                total_deleted += len(document_ids)

            if len(document_ids) < k:
                break
    except Exception as e:
        print(f"An error occurred during document deletion: {e}")
    return total_deleted

def delete_documents_by_ids(ids: List[str]) -> int:
    """Delete documents by their IDs."""
    try:
        vectorstore.delete(ids=ids)
        return len(ids)
    except Exception as e:
        print(f"Error deleting documents by IDs: {e}")
        return 0

def create_delete_prompt(query: str, result: str) -> str:
    """Create the prompt for delete operation."""
    character_prompt = read_prompt_from_file('character.md')
    delete_prompt = read_prompt_from_file('deletememory.md')
    return f"{character_prompt}\n\n{delete_prompt}".replace('{deleted_data}', query).replace('{delete_result}', result)

def create_save_prompt(query: str, result: str) -> str:
    """Create the prompt for save operation."""
    character_prompt = read_prompt_from_file('character.md')
    save_prompt = read_prompt_from_file('savememory.md')
    return f"{character_prompt}\n\n{save_prompt}".replace('{save_data}', query).replace('{save_result}', result)
