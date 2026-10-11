from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


# Embedding model
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


# ChromaDB vector store
vector_store = Chroma(
    collection_name="meeting_documents",
    embedding_function=embeddings,
    persist_directory="./chroma_db"
)