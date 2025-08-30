#!/usr/bin/env python3
"""
Process existing documents in the database and create vector store
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scribbleintimeai.settings')
django.setup()

from pathlib import Path
from scribble.models import KnowledgeDocument
from scribble.ingest import load_documents, chunk_documents, create_or_update_vector_store
from django.core.cache import cache
import shutil

def main():
    print("Processing existing documents...")
    
    # Check if vector store already exists
    project_root = Path(__file__).resolve().parent
    vectorstore_path = project_root / "vectorstore"
    
    if vectorstore_path.exists():
        print("✓ Vector store already exists")
        return True
    
    # Get all documents from database
    documents = KnowledgeDocument.objects.all()
    print(f"Found {documents.count()} documents in database")
    
    if not documents.exists():
        print("No documents found in database")
        return False
    
    # Check knowledge base directory
    knowledge_base_path = project_root / "knowledge_base"
    if not knowledge_base_path.exists():
        print("Creating knowledge base directory...")
        knowledge_base_path.mkdir(exist_ok=True)
    
    # Copy documents from media to knowledge base if needed
    files_processed = []
    for doc in documents:
        try:
            # Get the file path
            if hasattr(doc.file, 'path'):
                source_path = doc.file.path
            else:
                source_path = os.path.join('media', str(doc.file))
            
            # Check if file exists
            if not os.path.exists(source_path):
                print(f"⚠ File not found: {source_path}")
                continue
            
            # Copy to knowledge base
            filename = os.path.basename(str(doc.file))
            dest_path = knowledge_base_path / filename
            
            if not dest_path.exists():
                print(f"Copying {filename} to knowledge base...")
                shutil.copy2(source_path, dest_path)
            
            files_processed.append(dest_path)
            print(f"✓ Processed: {filename}")
            
        except Exception as e:
            print(f"✗ Error processing {doc.file}: {e}")
    
    if not files_processed:
        print("No files to process")
        return False
    
    # Process documents using ingest module
    print("Loading documents...")
    try:
        loaded_docs = load_documents(str(knowledge_base_path))
        print(f"Loaded {len(loaded_docs)} document chunks")
        
        if loaded_docs:
            print("Chunking documents...")
            chunks = chunk_documents(loaded_docs)
            print(f"Created {len(chunks)} chunks")
            
            if chunks:
                print("Creating vector store...")
                vector_store = create_or_update_vector_store(chunks)
                
                if vector_store:
                    # Update cache
                    cache.set('DOCUMENTS_UPLOADED', True, timeout=None)
                    
                    # Update document status
                    for doc in documents:
                        doc.is_processed = True
                        doc.processing_error = None
                        doc.save()
                    
                    print("✓ Vector store created successfully!")
                    print("✓ Documents marked as processed")
                    print("✓ AI can now use the knowledge base")
                    return True
                else:
                    print("✗ Failed to create vector store")
                    return False
            else:
                print("✗ No chunks created")
                return False
        else:
            print("✗ No documents loaded")
            return False
            
    except Exception as e:
        print(f"✗ Error during processing: {e}")
        return False

if __name__ == '__main__':
    success = main()
    if success:
        print("\n🎉 Document processing completed successfully!")
        print("The AI should now be able to answer questions based on your documents.")
    else:
        print("\n❌ Document processing failed!")
        print("Check the error messages above for details.") 