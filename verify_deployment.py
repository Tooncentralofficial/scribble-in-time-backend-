#!/usr/bin/env python3
"""
Verify deployment is working correctly
"""
import os
import sys
import django
from pathlib import Path

def verify_database():
    """Verify database tables exist"""
    print("🗄️  Verifying database...")
    
    try:
        # Set up Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scribbleintimeai.settings')
        django.setup()
        
        from django.db import connection
        
        # Check for key tables
        required_tables = [
            'scribble_memoirformsubmission',
            'chat_knowledgedocument',
            'scribble_conversation',
            'chat_message'
        ]
        
        with connection.cursor() as cursor:
            for table in required_tables:
                cursor.execute(f"""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='{table}';
                """)
                result = cursor.fetchone()
                
                if result:
                    print(f"✅ {table} exists")
                else:
                    print(f"❌ {table} missing")
                    return False
        
        return True
        
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False

def verify_vectorstore():
    """Verify vector store directory exists"""
    print("\n📚 Verifying vector store...")
    
    vectorstore_path = Path("vectorstore")
    
    if vectorstore_path.exists():
        print("✅ Vector store directory exists")
        
        # Check for files
        index_file = vectorstore_path / "index.faiss"
        pkl_file = vectorstore_path / "index.pkl"
        
        if index_file.exists() and pkl_file.exists():
            index_size = index_file.stat().st_size
            pkl_size = pkl_file.stat().st_size
            
            if index_size > 0 and pkl_size > 0:
                print(f"✅ Vector store files exist and have content")
                print(f"   - index.faiss: {index_size} bytes")
                print(f"   - index.pkl: {pkl_size} bytes")
                return True
            else:
                print("⚠️  Vector store files exist but are empty")
                return False
        else:
            print("⚠️  Vector store directory exists but missing files")
            return False
    else:
        print("⚠️  Vector store directory does not exist")
        return False

def verify_dependencies():
    """Verify required dependencies are installed"""
    print("\n📦 Verifying dependencies...")
    
    required_packages = [
        'pypdf',
        'langchain',
        'faiss-cpu',
        'sentence-transformers'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        return False
    
    return True

def test_memoir_form():
    """Test memoir form functionality"""
    print("\n📝 Testing memoir form...")
    
    try:
        from scribble.models import MemoirFormSubmission
        
        # Try to create a test submission
        test_submission = MemoirFormSubmission(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            phone_number="1234567890",
            gender="other",
            theme="Test theme",
            subject="Test subject",
            main_themes="Test themes",
            key_life_events="Test events",
            audience="family_friends"
        )
        
        # Don't save, just test if the model works
        print("✅ Memoir form model is working")
        return True
        
    except Exception as e:
        print(f"❌ Memoir form test failed: {e}")
        return False

def main():
    print("🚀 Deployment Verification")
    print("=" * 40)
    
    checks = [
        ("Database Tables", verify_database),
        ("Vector Store", verify_vectorstore),
        ("Dependencies", verify_dependencies),
        ("Memoir Form", test_memoir_form)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ {check_name} check failed with exception: {e}")
            results.append((check_name, False))
    
    print("\n" + "=" * 40)
    print("📊 Verification Results:")
    
    all_passed = True
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {check_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 All checks passed! Deployment is working correctly.")
    else:
        print("⚠️  Some checks failed. Please review the issues above.")
        print("\n💡 Common fixes:")
        print("   - Run migrations: python manage.py migrate")
        print("   - Install dependencies: pip install -r requirements.txt")
        print("   - Process documents: python simple_process.py")

if __name__ == "__main__":
    main() 