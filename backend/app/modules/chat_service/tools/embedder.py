from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_qdrant import QdrantVectorStore
from app.config.settings import settings


def load_pdf_to_qdrant(
    pdf_path: str, 
    collection_name: str, 
    user_id: str, 
    session_id: str
) -> QdrantVectorStore:
    """Load a PDF file, split into chunks, and store in Qdrant vector database."""
    # Load PDF
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    
    # Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)
    
    # Add metadata to each chunk
    for chunk in chunks:
        chunk.metadata.update({
            "user_id": user_id,
            "session_id": session_id
        })
    
    # Create embeddings model
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    vector_store = QdrantVectorStore.from_documents(
        documents=chunks,
        embedding=embeddings,
        url=settings.qdrant_url,
        collection_name=collection_name,
    )
    
    return vector_store


def get_vector_store(collection_name: str) -> QdrantVectorStore:
    """Connect to an existing Qdrant collection."""
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    return QdrantVectorStore.from_existing_collection(
        embedding=embeddings,
        url=settings.qdrant_url,
        collection_name=collection_name,
    )