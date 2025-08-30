#!/usr/bin/env python3
"""
Simple script to process documents and create vector store
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scribbleintimeai.settings')
django.setup()

from pathlib import Path
from scribble.ingest import main as process_documents
from django.core.cache import cache

def main():
    print("Starting document processing...")
    
    # Check if knowledge base directory exists
    project_root = Path(__file__).resolve().parent
    knowledge_base_path = project_root / "knowledge_base"
    
    if not knowledge_base_path.exists():
        print(f"Knowledge base directory not found at {knowledge_base_path}")
        return False
    
    # List files in knowledge base
    files = list(knowledge_base_path.glob("*"))
    if not files:
        print("No files found in knowledge base directory")
        return False
    
    print(f"Found {len(files)} files in knowledge base:")
    for file in files:
        print(f"  - {file.name}")
    
    # Process documents
    try:
        success = process_documents()
        
        if success:
            # Update cache
            cache.set('DOCUMENTS_UPLOADED', True, timeout=None)
            
            print("Document processing completed successfully!")
            print("Vector store has been created/updated.")
            print("AI can now use the knowledge base to answer questions.")
            return True
        else:
            print("Document processing failed!")
            return False
            
    except Exception as e:
        print(f"Error during document processing: {str(e)}")
        return False

if __name__ == '__main__':
    main() 