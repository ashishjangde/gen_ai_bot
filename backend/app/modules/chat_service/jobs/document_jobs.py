"""
Background jobs for document processing.
These run via Python RQ workers.
"""
import os
import tempfile
import httpx
from bs4 import BeautifulSoup
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, CSVLoader, TextLoader
from langchain_qdrant import QdrantVectorStore
from langchain.schema import Document
from app.config.settings import settings


def get_embeddings() -> HuggingFaceEmbeddings:
    """Get embeddings model"""
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


def download_from_oci(object_name: str) -> str:
    """Download file from OCI to temp location"""
    from app.config.oci_storage import OCIStorageService
    
    content = OCIStorageService.download_file(object_name)
    
    # Save to temp file
    ext = os.path.splitext(object_name)[1]
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    temp_file.write(content)
    temp_file.close()
    
    return temp_file.name


def process_pdf_job(
    source_id: str,
    file_path_or_oci: str,
    user_id: str,
    session_id: str,
    collection_name: str,
    is_oci: bool = False,
) -> dict:
    """
    Process a PDF file and store embeddings in Qdrant.
    Called by RQ worker.
    """
    file_path = file_path_or_oci
    
    try:
        # Download from OCI if needed
        if is_oci:
            file_path = download_from_oci(file_path_or_oci)
        
        # Load PDF
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        
        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )
        chunks = text_splitter.split_documents(documents)
        
        # Add metadata
        for chunk in chunks:
            chunk.metadata.update({
                "user_id": user_id,
                "session_id": session_id,
                "source_id": source_id,
                "source_type": "pdf",
            })
        
        # Create embeddings and store
        embeddings = get_embeddings()
        QdrantVectorStore.from_documents(
            documents=chunks,
            embedding=embeddings,
            url=settings.qdrant_url,
            collection_name=collection_name,
        )
        
        # Cleanup temp file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return {
            "status": "ready",
            "chunks": len(chunks),
            "pages": len(documents),
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
        }


def process_csv_job(
    source_id: str,
    file_path_or_oci: str,
    user_id: str,
    session_id: str,
    collection_name: str,
    is_oci: bool = False,
) -> dict:
    """Process a CSV file and store embeddings in Qdrant."""
    file_path = file_path_or_oci
    
    try:
        if is_oci:
            file_path = download_from_oci(file_path_or_oci)
        
        loader = CSVLoader(file_path)
        documents = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
        )
        chunks = text_splitter.split_documents(documents)
        
        for chunk in chunks:
            chunk.metadata.update({
                "user_id": user_id,
                "session_id": session_id,
                "source_id": source_id,
                "source_type": "csv",
            })
        
        embeddings = get_embeddings()
        QdrantVectorStore.from_documents(
            documents=chunks,
            embedding=embeddings,
            url=settings.qdrant_url,
            collection_name=collection_name,
        )
        
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return {
            "status": "ready",
            "chunks": len(chunks),
            "rows": len(documents),
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
        }


def process_text_job(
    source_id: str,
    file_path_or_oci: str,
    user_id: str,
    session_id: str,
    collection_name: str,
    is_oci: bool = False,
) -> dict:
    """Process a text file (TXT, MD, JSON) and store embeddings in Qdrant."""
    file_path = file_path_or_oci
    
    try:
        if is_oci:
            file_path = download_from_oci(file_path_or_oci)
        
        # Load text file
        loader = TextLoader(file_path)
        documents = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )
        chunks = text_splitter.split_documents(documents)
        
        for chunk in chunks:
            chunk.metadata.update({
                "user_id": user_id,
                "session_id": session_id,
                "source_id": source_id,
                "source_type": "txt",
            })
        
        embeddings = get_embeddings()
        QdrantVectorStore.from_documents(
            documents=chunks,
            embedding=embeddings,
            url=settings.qdrant_url,
            collection_name=collection_name,
        )
        
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return {
            "status": "ready",
            "chunks": len(chunks),
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
        }


def scrape_web_job(
    source_id: str,
    url: str,
    user_id: str,
    session_id: str,
    collection_name: str,
) -> dict:
    """Scrape a web page and store embeddings in Qdrant."""
    try:
        response = httpx.get(url, timeout=30, follow_redirects=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        text = soup.get_text(separator="\n", strip=True)
        title = soup.title.string if soup.title else url
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )
        
        documents = [Document(page_content=text, metadata={"url": url, "title": title})]
        chunks = text_splitter.split_documents(documents)
        
        for chunk in chunks:
            chunk.metadata.update({
                "user_id": user_id,
                "session_id": session_id,
                "source_id": source_id,
                "source_type": "web",
            })
        
        embeddings = get_embeddings()
        QdrantVectorStore.from_documents(
            documents=chunks,
            embedding=embeddings,
            url=settings.qdrant_url,
            collection_name=collection_name,
        )
        
        return {
            "status": "ready",
            "chunks": len(chunks),
            "title": title,
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
        }


def extract_memory_job(user_id: str, content: str) -> dict:
    """Extract and store facts to Mem0 long-term memory."""
    try:
        from app.modules.chat_service.services.memory_service import LongTermMemory
        
        result = LongTermMemory.add_memory(user_id, content)
        
        return {
            "status": "success",
            "memory_id": result.get("id") if result else None,
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
        }

