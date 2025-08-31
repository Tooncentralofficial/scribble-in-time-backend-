#!/usr/bin/env python3
"""
Check migration status and help diagnose issues
"""
import os
import sys
import django
from pathlib import Path

def check_migrations():
    """Check the status of migrations"""
    print("🔍 Checking migration status...")
    
    # Set up Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scribbleintimeai.settings')
    django.setup()
    
    from django.db import connection
    from django.core.management import execute_from_command_line
    
    try:
        # Check if the memoir form table exists
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
                
                # Check what tables do exist
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name LIKE 'scribble_%';
                """)
                scribble_tables = cursor.fetchall()
                
                print(f"📋 Existing scribble tables: {[table[0] for table in scribble_tables]}")
                
                # Check migration status
                print("\n📊 Checking migration status...")
                try:
                    execute_from_command_line(['manage.py', 'showmigrations', 'scribble'])
                except Exception as e:
                    print(f"⚠️  Could not check migration status: {e}")
                
                return False
                
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return False

def run_migrations():
    """Run migrations"""
    print("\n🔄 Running migrations...")
    
    try:
        from django.core.management import execute_from_command_line
        execute_from_command_line(['manage.py', 'migrate'])
        print("✅ Migrations completed")
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def check_migration_files():
    """Check if migration files exist"""
    print("\n📁 Checking migration files...")
    
    scribble_migrations_dir = Path("scribble/migrations")
    
    if not scribble_migrations_dir.exists():
        print("❌ scribble/migrations directory does not exist")
        return False
    
    migration_files = list(scribble_migrations_dir.glob("*.py"))
    migration_files = [f for f in migration_files if f.name != "__init__.py"]
    
    print(f"📋 Found {len(migration_files)} migration files:")
    for migration_file in migration_files:
        print(f"   - {migration_file.name}")
    
    # Check for the memoir form migration specifically
    memoir_migration = scribble_migrations_dir / "0003_memoirformsubmission.py"
    if memoir_migration.exists():
        print("✅ Memoir form migration file exists")
        return True
    else:
        print("❌ Memoir form migration file missing")
        return False

def main():
    print("🚀 Migration Status Check")
    print("=" * 40)
    
    # Check migration files
    files_ok = check_migration_files()
    
    # Check database
    table_exists = check_migrations()
    
    if not table_exists and files_ok:
        print("\n🔄 Table missing but migration file exists. Running migrations...")
        if run_migrations():
            # Check again
            table_exists = check_migrations()
    
    print("\n" + "=" * 40)
    if table_exists:
        print("✅ All good! Memoir form table exists.")
    else:
        print("❌ Issues found:")
        if not files_ok:
            print("   - Migration files are missing")
        if not table_exists:
            print("   - Database table is missing")
        
        print("\n💡 Try running:")
        print("   python manage.py makemigrations")
        print("   python manage.py migrate")

if __name__ == "__main__":
    main() 