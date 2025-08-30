#!/usr/bin/env python3
"""
Process the existing PDF file in knowledge base folder
"""
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scribbleintimeai.settings')

import django
django.setup()

def main():
    print("Processing existing PDF file...")
    
    # Check if PDF exists
    pdf_path = project_root / "knowledge_base" / "Uche AI Full Training Data Set.pdf"
    
    if not pdf_path.exists():
        print(f"PDF file not found at: {pdf_path}")
        return False
    
    print(f"Found PDF: {pdf_path}")
    print(f"File size: {pdf_path.stat().st_size} bytes")
    
    try:
        # Import the ingest functions
        from scribble.ingest import load_documents, chunk_documents, create_or_update_vector_store
        
        # Load the PDF
        print("Loading PDF document...")
        documents = load_documents(str(project_root / "knowledge_base"))
        
        if not documents:
            print("No documents loaded from PDF")
            return False
        
        print(f"Loaded {len(documents)} document chunks from PDF")
        
        # Chunk the documents
        print("Chunking documents...")
        chunks = chunk_documents(documents)
        
        if not chunks:
            print("No chunks created from documents")
            return False
        
        print(f"Created {len(chunks)} chunks")
        
        # Create vector store
        print("Creating vector store...")
        vector_store = create_or_update_vector_store(chunks)
        
        if vector_store:
            # Update cache
            from django.core.cache import cache
            cache.set('DOCUMENTS_UPLOADED', True, timeout=None)
            
            print("✓ Vector store created successfully!")
            print("✓ AI can now use the knowledge base")
            
            # Check if vector store files were created
            vectorstore_path = project_root / "vectorstore"
            if vectorstore_path.exists():
                files = list(vectorstore_path.glob("*"))
                print(f"✓ Vector store files: {len(files)}")
                for file in files:
                    print(f"  - {file.name}")
            
            return True
        else:
            print("✗ Failed to create vector store")
            return False
            
    except Exception as e:
        print(f"✗ Error processing PDF: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    if success:
        print("\n🎉 PDF processing completed successfully!")
        print("The AI should now be able to answer questions based on the PDF content.")
    else:
        print("\n❌ PDF processing failed!")
        print("Check the error messages above for details.") 