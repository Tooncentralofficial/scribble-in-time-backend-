#!/usr/bin/env python3
"""
Check the status of documents in the database
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scribbleintimeai.settings')
django.setup()

from scribble.models import KnowledgeDocument
from pathlib import Path

def main():
    print("Checking documents in database...")
    
    # Get all documents
    documents = KnowledgeDocument.objects.all()
    print(f"Total documents in database: {documents.count()}")
    
    if not documents.exists():
        print("No documents found in database")
        return
    
    print("\nDocument Details:")
    print("-" * 80)
    
    for i, doc in enumerate(documents, 1):
        print(f"\n{i}. Document ID: {doc.id}")
        print(f"   File: {doc.file}")
        print(f"   Title: {doc.title}")
        print(f"   Uploaded: {doc.uploaded_at}")
        print(f"   Processed: {doc.is_processed}")
        
        if hasattr(doc, 'processing_error') and doc.processing_error:
            print(f"   Error: {doc.processing_error}")
        
        # Check if file exists
        try:
            if hasattr(doc.file, 'path'):
                file_path = doc.file.path
            else:
                file_path = os.path.join('media', str(doc.file))
            
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                print(f"   File exists: Yes ({file_size} bytes)")
            else:
                print(f"   File exists: No (path: {file_path})")
        except Exception as e:
            print(f"   File check error: {e}")
    
    # Check vector store
    print("\n" + "-" * 80)
    project_root = Path(__file__).resolve().parent
    vectorstore_path = project_root / "vectorstore"
    
    if vectorstore_path.exists():
        print("✓ Vector store exists")
        files = list(vectorstore_path.glob("*"))
        print(f"   Files: {len(files)}")
        for file in files:
            print(f"   - {file.name}")
    else:
        print("✗ Vector store does not exist")
    
    # Check knowledge base directory
    knowledge_base_path = project_root / "knowledge_base"
    if knowledge_base_path.exists():
        files = list(knowledge_base_path.glob("*"))
        print(f"\nKnowledge base directory: {len(files)} files")
        for file in files:
            print(f"   - {file.name}")
    else:
        print("\nKnowledge base directory does not exist")
    
    # Check cache
    from django.core.cache import cache
    documents_uploaded = cache.get('DOCUMENTS_UPLOADED', False)
    print(f"\nCache status: DOCUMENTS_UPLOADED = {documents_uploaded}")

if __name__ == '__main__':
    main() 