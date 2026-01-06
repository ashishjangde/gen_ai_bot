import logging
import  io
import  asyncio
import  polars as pl
from typing import List
from  pypdf import  PdfReader
from  langchain_core.documents import Document
from langchain_text_splitters import  RecursiveCharacterTextSplitter

logger = logging.Logger(__name__)

class DocProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            add_start_index=True,
        )
        
        self.DOCS_TYPES = {
            "pdf": self._process_pdf,
            "csv": self._process_csv,
            "excel": self._process_excel,
            "xlsx": self._process_excel,
            "xls": self._process_excel,
            "mdx": self._process_text,
            "md": self._process_text,
            "text": self._process_text,
            "txt": self._process_text,
        }

        async def process(self , doc_content : bytes , file_type : str ) -> List[Document]:
            file_type = file_type.lower().strip(".").replace("application/", "")
            handler = self.DOCS_TYPES.get(file_type)
            if not handler:
                logger.warning(f"Unknown file type '{file_type}', falling back to text processing")
                handler = self._process_text
            
            try:
                logger.info(f"Processing {file_type} document (in-memory)...")
                documents = await asyncio.to_thread(handler, doc_content)
                logger.info(f"Successfully processed {len(documents)} chunks from {file_type}")
                return documents
            except Exception as e:
                logger.error(f"Failed to embed {file_type}: {e}")
                return []
        
        def _process_pdf(self, content: bytes) -> List[Document]:
            """Extract text from PDF using pypdf (streams)."""
            text = ""
            try:
                pdf = PdfReader(io.BytesIO(content))
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
            except Exception as e:
                logger.error(f"Error parsing PDF: {e}")
                return []
                
            return self.text_splitter.create_documents([text])
        
        def _process_csv(self, content: bytes) -> List[Document]:
            """Parse CSV bytes into documents using Polars."""
            try:
                df = pl.read_csv(io.BytesIO(content))
                text_data = []
                for row in df.iter_rows(named=True):
                    row_str = "\n".join(f"{k}: {v}" for k, v in row.items() if v is not None)
                    text_data.append(row_str)
                return self.text_splitter.create_documents(text_data)
            except Exception as e:
                logger.error(f"Error parsing CSV: {e}")
                return []
        
        def _process_excel(self, content: bytes) -> List[Document]:
            """Parse Excel bytes into documents using Polars."""
            try:
                df = pl.read_excel(io.BytesIO(content))
                text_data = []
                for row in df.iter_rows(named=True):
                    row_str = "\n".join(f"{k}: {v}" for k, v in row.items() if v is not None)
                    text_data.append(row_str)
                return self.text_splitter.create_documents(text_data)
            except Exception as e:
                logger.error(f"Error parsing Excel: {e}")
                return []
        
        def _process_text(self, content: bytes) -> List[Document]:
            """Parse plain text/markdown bytes."""
            try:
                text = content.decode("utf-8", errors="ignore")
                return self.text_splitter.create_documents([text])
            except Exception as e:
                logger.error(f"Error parsing text: {e}")
                return []
        