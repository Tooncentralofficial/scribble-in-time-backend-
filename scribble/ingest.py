import os
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
import os
from pathlib import Path

# Get the project root directory (where manage.py is located)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
VECTOR_STORE_PATH = str(PROJECT_ROOT / "vectorstore")

# Initialize embeddings as None - will be loaded when needed
_embeddings = None

def get_embeddings():
    """Lazily load and return the embeddings model"""
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)
    return _embeddings

def load_documents(docs_dir: str = "knowledge_base"):
    """
    Load documents from the knowledge base directory with detailed logging.
    
    Args:
        docs_dir: Directory containing the documents to load
        
    Returns:
        List of loaded document objects
    """
    import sys
    import logging
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger(__name__)
    
    documents = []
    docs_path = Path(docs_dir).resolve()
    
    logger.info(f"Loading documents from: {docs_path}")
    
    if not docs_path.exists():
        os.makedirs(docs_path, exist_ok=True)
        logger.warning(f"Created {docs_dir} directory. Please add your documents here.")
        return []
    
    # Get list of files in directory
    try:
        files = [f for f in docs_path.glob("*") if f.is_file()]
        logger.info(f"Found {len(files)} files in {docs_dir}")
    except Exception as e:
        logger.error(f"Error listing files in {docs_dir}: {str(e)}")
        return []
    
    if not files:
        logger.warning(f"No files found in {docs_dir}")
        return []
    
    for file_path in files:
        file_name = file_path.name
        try:
            logger.info(f"Processing file: {file_name}")
            
            # Check file exists and has content
            if not file_path.exists():
                logger.warning(f"File not found: {file_path}")
                continue
                
            file_size = file_path.stat().st_size
            logger.debug(f"File size: {file_size} bytes")
                
            if file_size == 0:
                logger.warning(f"Skipping empty file: {file_path}")
                continue
                
            # Load document based on file type
            loader = None
            try:
                if file_path.suffix.lower() == ".pdf":
                    logger.info("Initializing PDF loader...")
                    loader = PyPDFLoader(str(file_path))
                    logger.info("PDF loader initialized")
                elif file_path.suffix.lower() in [".txt", ".md"]:
                    logger.info("Initializing text loader...")
                    loader = TextLoader(str(file_path), autodetect_encoding=True)
                    logger.info("Text loader initialized")
                else:
                    logger.warning(f"Unsupported file format: {file_path.suffix}")
                    continue
                    
                # Load and validate documents
                logger.info("Loading document content...")
                loaded_docs = loader.load()
                logger.info(f"Loaded {len(loaded_docs) if loaded_docs else 0} pages")
                
                if not loaded_docs:
                    logger.warning(f"No content loaded from {file_name}")
                    # Try reading raw content as fallback
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if content.strip():
                                from langchain.schema import Document
                                loaded_docs = [Document(page_content=content, metadata={"source": str(file_path)})]
                                logger.info("Successfully loaded content using fallback method")
                    except Exception as read_error:
                        logger.error(f"Fallback content reading failed: {str(read_error)}")
                    
                    if not loaded_docs:
                        continue
                
                # Log first 100 chars of content for verification
                for i, doc in enumerate(loaded_docs):
                    logger.debug(f"Page {i+1} preview: {doc.page_content[:100]}...")
                    
                documents.extend(loaded_docs)
                logger.info(f"Successfully added {len(loaded_docs)} pages from {file_name}")
                
            except Exception as loader_error:
                logger.error(f"Error in document loader for {file_name}: {str(loader_error)}", exc_info=True)
                continue
                
        except Exception as e:
            logger.error(f"Unexpected error processing {file_name}: {str(e)}", exc_info=True)
            continue
    
    logger.info(f"Completed loading. Total documents loaded: {len(documents)}")
    return documents

def chunk_documents(documents):
    """
    Split documents into chunks with validation and error handling.
    
    Args:
        documents: List of document objects to split
        
    Returns:
        List of document chunks
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if not documents:
        logger.warning("No documents provided for chunking")
        return []
        
    logger.info(f"Starting to chunk {len(documents)} documents...")
    
    # Filter out any None or invalid documents
    valid_docs = []
    for i, doc in enumerate(documents):
        try:
            if not doc:
                logger.warning(f"Skipping None document at index {i}")
                continue
                
            if not hasattr(doc, 'page_content'):
                logger.warning(f"Document at index {i} has no 'page_content' attribute")
                continue
                
            if not isinstance(doc.page_content, str):
                logger.warning(f"Document at index {i} has non-string page_content")
                continue
                
            if not doc.page_content.strip():
                logger.warning(f"Document at index {i} has empty page_content")
                continue
                
            valid_docs.append(doc)
            
        except Exception as e:
            logger.error(f"Error validating document at index {i}: {str(e)}", exc_info=True)
    
    if not valid_docs:
        logger.error("No valid documents found to process")
        return []
    
    # Try different splitting strategies
    split_strategies = [
        {
            'name': 'RecursiveCharacterTextSplitter',
            'splitter': RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP,
                length_function=len,
            )
        },
        {
            'name': 'CharacterTextSplitter (double newline)',
            'splitter': lambda: CharacterTextSplitter(
                separator="\n\n",
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP,
                length_function=len,
            )
        },
        {
            'name': 'CharacterTextSplitter (single newline)',
            'splitter': lambda: CharacterTextSplitter(
                separator="\n",
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP,
                length_function=len,
            )
        },
        {
            'name': 'CharacterTextSplitter (space)',
            'splitter': lambda: CharacterTextSplitter(
                separator=" ",
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP,
                length_function=len,
            )
        }
    ]
    
    for strategy in split_strategies:
        try:
            logger.info(f"Trying {strategy['name']}...")
            splitter = strategy['splitter']
            
            # Handle both callable and instantiated splitters
            if callable(splitter):
                splitter = splitter()
                
            chunks = splitter.split_documents(valid_docs)
            
            if chunks and len(chunks) > 0:
                logger.info(f"Successfully created {len(chunks)} chunks using {strategy['name']}")
                
                # Log sample chunks for verification
                for i, chunk in enumerate(chunks[:3]):  # First 3 chunks
                    preview = chunk.page_content[:100].replace('\n', ' ').strip()
                    logger.debug(f"Chunk {i+1} preview: {preview}...")
                    
                return chunks
                
        except Exception as e:
            logger.warning(f"{strategy['name']} failed: {str(e)}")
            continue
    
    logger.error("All chunking strategies failed")
    return []

def create_vector_store(chunks):
    """Create and save FAISS vector store."""
    # Get embeddings (will be loaded if not already)
    embeddings = get_embeddings()
    
    # Create and save vector store
    vectorstore = FAISS.from_documents(chunks, embeddings)
    os.makedirs(VECTOR_STORE_PATH, exist_ok=True)
    vectorstore.save_local(VECTOR_STORE_PATH)
    return vectorstore

def create_or_update_vector_store(chunks):
    """
    Create or update the FAISS vector store with comprehensive error handling.
    
    Args:
        chunks: List of document chunks to index
        
    Returns:
        FAISS vector store instance or None if failed
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if not chunks:
        logger.error("No chunks provided for vector store")
        return None
        
    logger.info(f"Starting vector store creation/update with {len(chunks)} chunks")
    
    try:
        # Get embeddings (will be loaded if not already)
        logger.info(f"Initializing embeddings with model: {MODEL_NAME}")
        embeddings = get_embeddings()
        
        # Ensure vector store directory exists
        os.makedirs(VECTOR_STORE_PATH, exist_ok=True)
        index_file = os.path.join(VECTOR_STORE_PATH, "index.faiss")
        
        # Try to load existing vector store if it exists
        if os.path.exists(index_file):
            try:
                logger.info("Loading existing vector store...")
                vectorstore = FAISS.load_local(
                    VECTOR_STORE_PATH, 
                    embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info("Successfully loaded existing vector store")
                
                # Add new chunks
                logger.info(f"Adding {len(chunks)} new chunks to existing vector store")
                try:
                    if hasattr(vectorstore, 'add_documents') and callable(vectorstore.add_documents):
                        vectorstore.add_documents(chunks)
                        logger.info("Successfully added documents to existing vector store")
                    else:
                        logger.warning("add_documents not available, creating new vector store")
                        vectorstore = FAISS.from_documents(chunks, embeddings)
                except Exception as add_error:
                    logger.error(f"Error adding documents: {str(add_error)}")
                    logger.info("Creating new vector store after add_documents failed")
                    vectorstore = FAISS.from_documents(chunks, embeddings)
                
            except Exception as load_error:
                logger.error(f"Error loading existing vector store: {str(load_error)}")
                logger.info("Creating new vector store")
                vectorstore = FAISS.from_documents(chunks, embeddings)
        else:
            logger.info("Creating new vector store")
            vectorstore = FAISS.from_documents(chunks, embeddings)
        
        # Save the vector store
        logger.info("Saving vector store...")
        try:
            vectorstore.save_local(VECTOR_STORE_PATH)
            logger.info(f"Vector store saved to {VECTOR_STORE_PATH}")
            
            # Verify the save
            if not os.path.exists(index_file):
                raise Exception("Vector store file was not created")
                
            return vectorstore
            
        except Exception as save_error:
            logger.error(f"Error saving vector store: {str(save_error)}")
            # Try to save to a temporary location as fallback
            try:
                temp_path = os.path.join(VECTOR_STORE_PATH, "temp_index")
                vectorstore.save_local(temp_path)
                logger.warning(f"Saved to temporary location: {temp_path}")
                return vectorstore
            except Exception as temp_error:
                logger.error(f"Failed to save to temporary location: {str(temp_error)}")
                return None
                
    except Exception as e:
        logger.error(f"Critical error in create_or_update_vector_store: {str(e)}", exc_info=True)
        return None

def main():
    """
    Main function to load, chunk, and index documents with comprehensive error handling.
    """
    try:
        print("=" * 50)
        print("Starting document processing...")
        print("-" * 50)
        
        # Step 1: Load documents
        print("\n[1/3] Loading documents...")
        documents = load_documents()
        
        if not documents:
            print("\nError: No valid documents found to process.")
            print("Please add documents to the knowledge_base/ directory.")
            return False
        
        print(f"\n✓ Successfully loaded {len(documents)} documents")
        
        # Step 2: Chunk documents
        print("\n[2/3] Chunking documents...")
        chunks = chunk_documents(documents)
        
        if not chunks:
            print("\nError: Failed to create chunks from documents.")
            print("This might be due to empty documents or unsupported content.")
            return False
        
        print(f"\n✓ Created {len(chunks)} chunks from documents")
        
        # Step 3: Create/update vector store
        print("\n[3/3] Creating/updating vector store...")
        try:
            vector_store = create_or_update_vector_store(chunks)
            if vector_store is None:
                raise Exception("Vector store creation returned None")
                
            print("\n✓ Vector store created/updated successfully!")
            print("\nDocument processing completed successfully!")
            print("=" * 50)
            return True
            
        except Exception as e:
            print("\nError: Failed to create/update vector store")
            print(f"Details: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print("\nAn unexpected error occurred during document processing:")
        print(str(e))
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
