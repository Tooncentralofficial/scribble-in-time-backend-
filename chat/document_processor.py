import os
import logging
from pathlib import Path
from django.conf import settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
    UnstructuredWordDocumentLoader,
)
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Handles document processing and vector store management"""
    
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.vectorstore_path = os.path.join(settings.BASE_DIR, 'vectorstore')
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
    
    def load_document(self, file_path, file_type):
        """Load document based on file type"""
        try:
            if file_type == 'pdf':
                loader = PyPDFLoader(file_path)
            elif file_type == 'txt':
                loader = TextLoader(file_path, encoding='utf-8')
            elif file_type == 'md':
                loader = UnstructuredMarkdownLoader(file_path)
            elif file_type == 'docx':
                loader = UnstructuredWordDocumentLoader(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
                
            return loader.load()
        except Exception as e:
            logger.error(f"Error loading document {file_path}: {str(e)}")
            raise
    
    def create_or_update_vector_store(self, documents):
        """Create or update the vector store with new documents"""
        try:
            if os.path.exists(self.vectorstore_path):
                # Load existing vector store
                vectorstore = FAISS.load_local(
                    self.vectorstore_path, 
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                # Add new documents
                vectorstore.add_documents(documents)
                logger.info(f"Updated existing vector store with {len(documents)} new documents")
            else:
                # Create new vector store
                vectorstore = FAISS.from_documents(documents, self.embeddings)
                logger.info(f"Created new vector store with {len(documents)} documents")
            
            # Save the updated vector store
            vectorstore.save_local(self.vectorstore_path)
            return vectorstore
            
        except Exception as e:
            logger.error(f"Error in create_or_update_vector_store: {str(e)}")
            raise
    
    def process_document(self, document):
        """Process a document and update the vector store"""
        try:
            # Load the document
            docs = self.load_document(document.file.path, document.file_type)
            
            # Split documents into chunks
            splits = self.text_splitter.split_documents(docs)
            logger.info(f"Created {len(splits)} chunks from the document")
            
            # Update or create vector store with new chunks
            self.create_or_update_vector_store(splits)
            
            # Update document status
            document.is_processed = True
            document.save()
            
            # Update cache
            from django.core.cache import cache
            cache.set('DOCUMENTS_UPLOADED', True, timeout=None)
            
            logger.info(f"Successfully processed document: {document.title}")
            return True
            
        except Exception as e:
            error_msg = f"Error processing document {document.id}: {str(e)}"
            logger.error(error_msg)
            document.processing_error = error_msg
            document.is_processed = False
            document.save()
            return False
