#!/usr/bin/env python3
"""
Clean up vector store directory and remove any corrupted files
"""
import os
import shutil
from pathlib import Path

def clean_vectorstore():
    """Clean up the vector store directory"""
    print("🧹 Cleaning vector store directory...")
    
    # Get project root
    project_root = Path(__file__).resolve().parent
    vectorstore_path = project_root / "vectorstore"
    
    print(f"Vector store path: {vectorstore_path}")
    
    if vectorstore_path.exists():
        print("📁 Vector store directory exists, checking for issues...")
        
        # Check for required files
        index_file = vectorstore_path / "index.faiss"
        pkl_file = vectorstore_path / "index.pkl"
        
        issues_found = False
        
        # Check if files exist but are empty
        if index_file.exists():
            size = index_file.stat().st_size
            print(f"📊 index.faiss size: {size} bytes")
            if size == 0:
                print("⚠️  index.faiss is empty, will remove")
                issues_found = True
        else:
            print("❌ index.faiss missing")
            issues_found = True
            
        if pkl_file.exists():
            size = pkl_file.stat().st_size
            print(f"📊 index.pkl size: {size} bytes")
            if size == 0:
                print("⚠️  index.pkl is empty, will remove")
                issues_found = True
        else:
            print("❌ index.pkl missing")
            issues_found = True
        
        if issues_found:
            print("\n🗑️  Removing vector store directory due to issues...")
            shutil.rmtree(vectorstore_path)
            print("✅ Vector store directory removed")
        else:
            print("✅ Vector store appears to be valid")
            return True
    else:
        print("📁 Vector store directory does not exist")
    
    # Create fresh directory
    print("📁 Creating fresh vector store directory...")
    vectorstore_path.mkdir(exist_ok=True)
    
    # Create a placeholder file
    placeholder_file = vectorstore_path / ".placeholder"
    placeholder_file.write_text("Vector store directory - ready for documents")
    print("📄 Created placeholder file")
    
    return True

def main():
    print("🚀 Vector Store Cleanup")
    print("=" * 30)
    
    success = clean_vectorstore()
    
    if success:
        print("\n✅ Vector store cleanup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Upload a document through the web interface")
        print("2. The system will create a new vector store automatically")
    else:
        print("\n❌ Vector store cleanup failed!")

if __name__ == "__main__":
    main() 