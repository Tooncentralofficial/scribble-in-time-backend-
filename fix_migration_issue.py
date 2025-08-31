#!/usr/bin/env python3
"""
Fix migration issue and ensure memoir form table exists
"""
import os
import sys
import subprocess
import django
from pathlib import Path

def setup_django():
    """Set up Django environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scribbleintimeai.settings')
    django.setup()

def check_table_exists():
    """Check if the memoir form table exists"""
    try:
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='scribble_memoirformsubmission';
            """)
            result = cursor.fetchone()
            
            if result:
                print("✅ scribble_memoirformsubmission table exists")
                return True
            else:
                print("❌ scribble_memoirformsubmission table does not exist")
                return False
    except Exception as e:
        print(f"❌ Error checking table: {e}")
        return False

def run_migrations():
    """Run Django migrations"""
    print("🔄 Running migrations...")
    
    try:
        # First, make migrations
        print("📝 Making migrations...")
        result = subprocess.run(
            [sys.executable, 'manage.py', 'makemigrations'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✅ Makemigrations completed")
            print(f"Output: {result.stdout}")
        else:
            print("⚠️  Makemigrations had issues:")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
        
        # Then run migrations
        print("🚀 Running migrations...")
        result = subprocess.run(
            [sys.executable, 'manage.py', 'migrate'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print("✅ Migrations completed successfully")
            print(f"Output: {result.stdout}")
            return True
        else:
            print("❌ Migrations failed:")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        return False

def create_table_manually():
    """Create the table manually if migrations fail"""
    print("🔧 Creating table manually...")
    
    try:
        from django.db import connection
        from django.conf import settings
        
        # Check if we're using PostgreSQL (Railway) or SQLite
        db_engine = settings.DATABASES['default']['ENGINE']
        
        if 'postgresql' in db_engine:
            # PostgreSQL syntax for Railway
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS scribble_memoirformsubmission (
                id SERIAL PRIMARY KEY,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                email VARCHAR(254) NOT NULL,
                phone_number VARCHAR(20) NOT NULL,
                gender VARCHAR(20) NOT NULL,
                theme VARCHAR(200) NOT NULL,
                subject VARCHAR(200) NOT NULL,
                main_themes TEXT NOT NULL,
                key_life_events TEXT NOT NULL,
                audience VARCHAR(20) NOT NULL,
                submitted_at TIMESTAMP WITH TIME ZONE NOT NULL,
                is_processed BOOLEAN NOT NULL DEFAULT FALSE,
                processing_notes TEXT NULL
            );
            """
        else:
            # SQLite syntax
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS scribble_memoirformsubmission (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                email VARCHAR(254) NOT NULL,
                phone_number VARCHAR(20) NOT NULL,
                gender VARCHAR(20) NOT NULL,
                theme VARCHAR(200) NOT NULL,
                subject VARCHAR(200) NOT NULL,
                main_themes TEXT NOT NULL,
                key_life_events TEXT NOT NULL,
                audience VARCHAR(20) NOT NULL,
                submitted_at DATETIME NOT NULL,
                is_processed BOOLEAN NOT NULL DEFAULT 0,
                processing_notes TEXT NULL
            );
            """
        
        with connection.cursor() as cursor:
            cursor.execute(create_table_sql)
            print(f"✅ Table created manually using {db_engine}")
            return True
            
    except Exception as e:
        print(f"❌ Error creating table manually: {e}")
        return False

def main():
    print("🚀 Fixing Migration Issue")
    print("=" * 40)
    
    # Set up Django
    setup_django()
    
    # Check if table exists
    if check_table_exists():
        print("\n🎉 Table already exists! No action needed.")
        return True
    
    # Try running migrations
    print("\n🔄 Attempting to run migrations...")
    if run_migrations():
        # Check again
        if check_table_exists():
            print("\n🎉 Success! Table created via migrations.")
            return True
    
    # If migrations failed, try manual creation
    print("\n🔧 Migrations failed, trying manual table creation...")
    if create_table_manually():
        if check_table_exists():
            print("\n🎉 Success! Table created manually.")
            return True
    
    print("\n❌ Failed to create table. Please check the logs above.")
    return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Migration issue fixed!")
    else:
        print("\n💥 Migration issue could not be resolved.")
        sys.exit(1) 