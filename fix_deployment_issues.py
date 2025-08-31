#!/usr/bin/env python3
"""
Fix deployment issues script
"""
import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed:")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} failed with exception: {str(e)}")
        return False

def install_dependencies():
    """Install missing dependencies"""
    print("\n📦 Installing missing dependencies...")
    
    # Install pypdf
    if not run_command("pip install pypdf==4.3.0", "Installing pypdf"):
        return False
    
    # Install python-multipart for better file upload handling
    if not run_command("pip install python-multipart", "Installing python-multipart"):
        return False
    
    # Update requirements.txt
    requirements_file = Path("requirements.txt")
    if requirements_file.exists():
        with open(requirements_file, "r") as f:
            content = f.read()
        
        if "pypdf==4.3.0" not in content:
            with open(requirements_file, "a") as f:
                f.write("\npypdf==4.3.0\npython-multipart==0.0.9\n")
            print("✅ Updated requirements.txt")
    
    return True

def run_migrations():
    """Run Django migrations"""
    print("\n🗄️ Running Django migrations...")
    
    # Try multiple approaches
    commands = [
        "python manage.py migrate",
        "python -m django manage.py migrate",
        "python manage.py makemigrations && python manage.py migrate"
    ]
    
    for i, command in enumerate(commands, 1):
        print(f"\n🔄 Attempt {i}: {command}")
        if run_command(command, f"Migration attempt {i}"):
            return True
        time.sleep(2)  # Wait between attempts
    
    return False

def check_database():
    """Check if the memoir form table exists"""
    print("\n🔍 Checking database tables...")
    
    try:
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scribbleintimeai.settings')
        django.setup()
        
        from scribble.models import MemoirFormSubmission
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='scribble_memoirformsubmission';
            """)
            result = cursor.fetchone()
            
            if result:
                print("✅ Memoir form table exists")
                return True
            else:
                print("❌ Memoir form table does not exist")
                return False
                
    except Exception as e:
        print(f"❌ Error checking database: {str(e)}")
        return False

def main():
    print("🚀 Fixing deployment issues...")
    print("=" * 50)
    
    # Step 1: Install dependencies
    if not install_dependencies():
        print("\n❌ Failed to install dependencies")
        return False
    
    # Step 2: Run migrations
    if not run_migrations():
        print("\n❌ Failed to run migrations")
        print("\n💡 Manual steps to try:")
        print("1. Close any running Python processes")
        print("2. Restart your terminal/command prompt")
        print("3. Run: python manage.py migrate")
        return False
    
    # Step 3: Check database
    if not check_database():
        print("\n❌ Database table check failed")
        return False
    
    print("\n🎉 All issues fixed successfully!")
    print("\n📋 Summary:")
    print("- ✅ Dependencies installed")
    print("- ✅ Migrations completed")
    print("- ✅ Database tables verified")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n💥 Some issues could not be resolved automatically.")
        print("Please try the manual steps mentioned above.")
        sys.exit(1) 