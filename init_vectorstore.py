#!/usr/bin/env python3
"""
Initialize vector store directory and handle any existing issues
"""
import os
import shutil
from pathlib import Path

def init_vectorstore():
    """Initialize the vector store directory"""
    print("🔧 Initializing vector store...")
    
    # Get project root
    project_root = Path(__file__).resolve().parent
    vectorstore_path = project_root / "vectorstore"
    
    print(f"Vector store path: {vectorstore_path}")
    
    # Check if vector store directory exists
    if vectorstore_path.exists():
        print("📁 Vector store directory exists")
        
        # Check for required files
        index_file = vectorstore_path / "index.faiss"
        pkl_file = vectorstore_path / "index.pkl"
        
        if index_file.exists() and pkl_file.exists():
            print("✅ Vector store files exist")
            
            # Check file sizes
            index_size = index_file.stat().st_size
            pkl_size = pkl_file.stat().st_size
            
            print(f"📊 Index file size: {index_size} bytes")
            print(f"📊 PKL file size: {pkl_size} bytes")
            
            if index_size == 0 or pkl_size == 0:
                print("⚠️  One or more vector store files are empty")
                print("🗑️  Removing empty files...")
                
                if index_size == 0:
                    index_file.unlink()
                if pkl_size == 0:
                    pkl_file.unlink()
                    
                print("✅ Empty files removed")
            else:
                print("✅ Vector store appears to be valid")
                return True
        else:
            print("⚠️  Vector store directory exists but missing required files")
            if index_file.exists():
                print(f"   - index.faiss exists ({index_file.stat().st_size} bytes)")
            else:
                print("   - index.faiss missing")
                
            if pkl_file.exists():
                print(f"   - index.pkl exists ({pkl_file.stat().st_size} bytes)")
            else:
                print("   - index.pkl missing")
    else:
        print("📁 Vector store directory does not exist")
    
    # Create or recreate the directory
    print("📁 Creating vector store directory...")
    if vectorstore_path.exists():
        # Remove existing directory if it has issues
        shutil.rmtree(vectorstore_path)
        print("🗑️  Removed existing vector store directory")
    
    vectorstore_path.mkdir(exist_ok=True)
    print("✅ Vector store directory created")
    
    # Create a placeholder file to ensure the directory is not empty
    placeholder_file = vectorstore_path / ".placeholder"
    placeholder_file.write_text("Vector store directory - ready for documents")
    print("📄 Created placeholder file")
    
    return True

def check_documents():
    """Check for existing documents that need processing"""
    print("\n📚 Checking for existing documents...")
    
    project_root = Path(__file__).resolve().parent
    knowledge_base_path = project_root / "knowledge_base"
    
    if knowledge_base_path.exists():
        pdf_files = list(knowledge_base_path.glob("*.pdf"))
        txt_files = list(knowledge_base_path.glob("*.txt"))
        md_files = list(knowledge_base_path.glob("*.md"))
        
        total_files = len(pdf_files) + len(txt_files) + len(md_files)
        
        print(f"📊 Found {total_files} documents:")
        print(f"   - PDF files: {len(pdf_files)}")
        print(f"   - TXT files: {len(txt_files)}")
        print(f"   - MD files: {len(md_files)}")
        
        if total_files > 0:
            print("\n💡 To process these documents, run:")
            print("   python simple_process.py")
            print("   or")
            print("   python process_existing_docs.py")
    else:
        print("📁 Knowledge base directory does not exist")
    
    return total_files > 0

def main():
    print("🚀 Vector Store Initialization")
    print("=" * 40)
    
    # Initialize vector store
    init_success = init_vectorstore()
    
    # Check for documents
    has_documents = check_documents()
    
    print("\n" + "=" * 40)
    if init_success:
        print("✅ Vector store initialization completed successfully!")
        
        if has_documents:
            print("\n📋 Next steps:")
            print("1. Process existing documents: python simple_process.py")
            print("2. Or upload new documents through the web interface")
        else:
            print("\n📋 Next steps:")
            print("1. Upload documents through the web interface")
            print("2. Or place documents in the knowledge_base/ directory")
    else:
        print("❌ Vector store initialization failed!")
    
    print("\n🎉 Ready for document processing!")

if __name__ == "__main__":
    main() 