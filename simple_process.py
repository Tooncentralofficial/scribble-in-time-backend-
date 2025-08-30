#!/usr/bin/env python3
"""
Simple PDF processing without Django setup
"""
import os
import sys
from pathlib import Path

def main():
    print("Simple PDF processing...")
    
    # Check if PDF exists
    pdf_path = Path("knowledge_base/Uche AI Full Training Data Set.pdf")
    
    if not pdf_path.exists():
        print(f"PDF file not found at: {pdf_path}")
        return False
    
    print(f"Found PDF: {pdf_path}")
    print(f"File size: {pdf_path.stat().st_size} bytes")
    
    try:
        # Import required libraries
        from langchain_community.document_loaders import PyPDFLoader
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain_huggingface import HuggingFaceEmbeddings
        from langchain_community.vectorstores import FAISS
        
        # Load the PDF
        print("Loading PDF document...")
        loader = PyPDFLoader(str(pdf_path))
        documents = loader.load()
        
        if not documents:
            print("No documents loaded from PDF")
            return False
        
        print(f"Loaded {len(documents)} pages from PDF")
        
        # Chunk the documents
        print("Chunking documents...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
        )
        chunks = text_splitter.split_documents(documents)
        
        if not chunks:
            print("No chunks created from documents")
            return False
        
        print(f"Created {len(chunks)} chunks")
        
        # Create embeddings and vector store
        print("Creating embeddings and vector store...")
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vector_store = FAISS.from_documents(chunks, embeddings)
        
        # Save vector store
        print("Saving vector store...")
        vector_store.save_local("vectorstore")
        
        # Verify files were created
        if Path("vectorstore").exists():
            files = list(Path("vectorstore").glob("*"))
            print(f"✓ Vector store created with {len(files)} files:")
            for file in files:
                print(f"  - {file.name}")
            
            # Create a simple cache file to indicate documents are processed
            with open("documents_processed.txt", "w") as f:
                f.write("Documents have been processed and vector store is ready.")
            
            print("✓ Processing completed successfully!")
            print("✓ AI can now use the knowledge base")
            return True
        else:
            print("✗ Vector store directory not created")
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