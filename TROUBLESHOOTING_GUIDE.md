# Troubleshooting Guide

## Current Issues and Solutions

### 1. Missing Database Table Error
**Error**: `no such table: scribble_memoirformsubmission`

**Solution**: Run the Django migration to create the missing table.

**Options**:
- **Automatic**: Run `fix_deployment_issues.py`
- **Manual**: Run `python manage.py migrate`
- **Alternative**: Use `run_migration.bat` or `run_migration.ps1`

### 2. Missing PDF Dependencies
**Error**: `pypdf package not found, please install it with pip install pypdf`

**Solution**: Install the missing PDF processing dependencies.

**Options**:
- **Automatic**: Run `fix_deployment_issues.py`
- **Manual**: Run `pip install pypdf==4.3.0 python-multipart==0.0.9`

### 3. Python Process Lock
**Error**: `Program 'python.exe' failed to run: The process cannot access the file because it is being used by another process`

**Solution**: Close other Python processes and try again.

**Steps**:
1. Close any running Python processes
2. Restart your terminal/command prompt
3. Try running the commands again

## Quick Fix Commands

### Option 1: Automatic Fix (Recommended)
```bash
python fix_deployment_issues.py
```

### Option 2: Manual Steps
```bash
# Install dependencies
pip install pypdf==4.3.0 python-multipart==0.0.9

# Run migrations
python manage.py migrate
```

### Option 3: Using Batch/PowerShell Scripts
```bash
# Windows Batch
run_migration.bat

# PowerShell
.\run_migration.ps1
```

## Verification Steps

After running the fixes, verify everything is working:

1. **Check if memoir form table exists**:
   ```bash
   python manage.py shell
   ```
   ```python
   from scribble.models import MemoirFormSubmission
   print("Table exists!")
   ```

2. **Test document upload**:
   - Use the `test_upload.html` file in your browser
   - Or run: `python test_upload.py path/to/document.pdf`

3. **Test memoir form endpoints**:
   ```bash
   curl http://localhost:8000/api/memoir/options/
   ```

## Common Issues and Solutions

### Issue: Migration fails with "table already exists"
**Solution**: This is normal if the table was already created. The migration will skip it.

### Issue: PDF processing still fails after installing pypdf
**Solution**: Make sure you're using the correct import:
```python
# Use this import (not the deprecated one)
from langchain_huggingface import HuggingFaceEmbeddings
```

### Issue: File upload still shows "No file provided"
**Solution**: Make sure your frontend is using FormData correctly:
```javascript
const formData = new FormData();
formData.append('file', file); // Key must be 'file'
```

## Deployment Notes

For Railway deployment, these issues should be resolved by:

1. **Dependencies**: The updated `requirements.txt` includes `pypdf`
2. **Migrations**: The `docker_start.py` script runs migrations automatically
3. **Database**: Railway's PostgreSQL will be used instead of SQLite

## Support

If you continue to have issues:

1. Check the Django logs for detailed error messages
2. Verify all dependencies are installed: `pip list | grep pypdf`
3. Test the database connection: `python manage.py dbshell`
4. Contact support with the specific error messages 