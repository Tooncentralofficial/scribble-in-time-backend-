#!/usr/bin/env python3
"""
Check deployment configuration
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scribbleintimeai.settings')
django.setup()

from pathlib import Path

def main():
    print("Checking deployment configuration...")
    
    # Check 1: Static directory
    project_root = Path(__file__).resolve().parent
    static_dir = project_root / "static"
    
    if static_dir.exists():
        print("✓ Static directory exists")
        files = list(static_dir.glob("*"))
        if files:
            print(f"✓ Static directory has {len(files)} files")
        else:
            print("⚠ Static directory is empty")
    else:
        print("✗ Static directory missing")
    
    # Check 2: Model fields
    try:
        from scribble.models import KnowledgeDocument
        doc = KnowledgeDocument()
        
        required_fields = ['file', 'title', 'uploaded_at', 'is_processed']
        for field in required_fields:
            if hasattr(doc, field):
                print(f"✓ Field '{field}' exists")
            else:
                print(f"✗ Field '{field}' missing")
        
        # Check optional field
        if hasattr(doc, 'processing_error'):
            print("✓ Field 'processing_error' exists")
        else:
            print("⚠ Field 'processing_error' missing (will be added by migration)")
            
    except Exception as e:
        print(f"✗ Model check failed: {e}")
    
    # Check 3: Settings
    try:
        from django.conf import settings
        
        # Check static files settings
        if hasattr(settings, 'STATICFILES_DIRS'):
            print("✓ STATICFILES_DIRS configured")
        else:
            print("✗ STATICFILES_DIRS not configured")
        
        # Check required settings
        required_settings = ['SECRET_KEY', 'DEBUG', 'OPENROUTER_API_KEY']
        for setting in required_settings:
            if hasattr(settings, setting):
                print(f"✓ Setting '{setting}' configured")
            else:
                print(f"⚠ Setting '{setting}' not configured")
                
    except Exception as e:
        print(f"✗ Settings check failed: {e}")
    
    # Check 4: Admin configuration
    try:
        from django.contrib import admin
        from scribble.models import KnowledgeDocument
        
        # Check if admin is registered
        if admin.site.is_registered(KnowledgeDocument):
            print("✓ KnowledgeDocument admin registered")
        else:
            print("✗ KnowledgeDocument admin not registered")
            
    except Exception as e:
        print(f"✗ Admin check failed: {e}")
    
    print("\nDeployment check completed!")

if __name__ == '__main__':
    main() 