from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
import uuid

# Initialize OpenAI embeddings
embeddings = OpenAIEmbeddings()

# Initialize Chroma vector store
persist_directory = 'chroma_db'
vectorstore = Chroma(persist_directory=persist_directory,
                     embedding_function=embeddings)


def insert_document(data):
    id = str(uuid.uuid4())
    vectorstore.add_documents(
        documents=[Document(page_content=data, metadata={"id": id})], ids=[id])
    return id


def search_similarity(query, k=3):
    return vectorstore.similarity_search(query, k)


def search_similarity_threshold(query, k=3, threshold=0.5):
    return vectorstore.search(query, search_type="similarity_score_threshold", k=k, score_threshold=threshold)


def search_max_rel(query, k=3):
    return vectorstore.max_marginal_relevance_search(query, k)


def delete_documents_by_query(query: str, threshold=0.1):
    k = 100
    tot = 0
    try:
        while True:
            docs = search_similarity_threshold(query, k=k, threshold=threshold)
            document_ids = [result.metadata["id"] for result in docs]

            if document_ids:
                vectorstore.delete(ids=document_ids)
                tot += len(document_ids)

            if len(document_ids) < k:
                break
    except Exception as e:
        print(f"An error occurred during document deletion: {e}")
    return tot


def delete_documents_by_ids(ids: list[str]):
    vectorstore.delete(ids=ids)
    return len(ids)
