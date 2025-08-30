#!/usr/bin/env python3
"""
Script to fix deployment issues
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scribbleintimeai.settings')
django.setup()

from pathlib import Path

def main():
    print("Fixing deployment issues...")
    
    # Create static directory if it doesn't exist
    project_root = Path(__file__).resolve().parent
    static_dir = project_root / "static"
    
    if not static_dir.exists():
        print(f"Creating static directory: {static_dir}")
        static_dir.mkdir(exist_ok=True)
        
        # Create a simple CSS file to avoid empty directory issues
        css_file = static_dir / "style.css"
        with open(css_file, 'w') as f:
            f.write("/* Static files placeholder */\n")
    
    # Create staticfiles directory
    staticfiles_dir = project_root / "staticfiles"
    if not staticfiles_dir.exists():
        print(f"Creating staticfiles directory: {staticfiles_dir}")
        staticfiles_dir.mkdir(exist_ok=True)
    
    # Run migrations
    print("Running migrations...")
    try:
        from django.core.management import execute_from_command_line
        execute_from_command_line(['manage.py', 'migrate'])
        print("✓ Migrations completed successfully")
    except Exception as e:
        print(f"✗ Migration error: {str(e)}")
    
    # Collect static files
    print("Collecting static files...")
    try:
        from django.core.management import execute_from_command_line
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
        print("✓ Static files collected successfully")
    except Exception as e:
        print(f"✗ Static files error: {str(e)}")
    
    print("Deployment fixes completed!")

if __name__ == '__main__':
    main() 