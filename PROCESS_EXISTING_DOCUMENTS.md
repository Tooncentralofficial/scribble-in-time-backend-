# Process Existing Documents Guide

## Current Situation

You have documents in the database, but the AI is still saying "no context" because:
- ✅ Documents exist in the database
- ❌ Vector store doesn't exist (not created yet)
- ❌ Documents haven't been processed into embeddings

## The Problem

The AI needs a **vector store** to answer questions based on documents. The vector store contains:
- Document embeddings (vector representations)
- Chunked text for similarity search
- Metadata for context retrieval

Without the vector store, the AI can't search through the document content.

## Solution: Process Existing Documents

### Step 1: Check Current Status

First, let's see what documents you have:

```bash
python check_documents.py
```

This will show:
- Documents in the database
- Their processing status
- Whether vector store exists
- File locations

### Step 2: Process Documents

Run the document processing script:

```bash
python process_existing_docs.py
```

This script will:
1. Find all documents in the database
2. Copy them to the knowledge base directory
3. Load and chunk the documents
4. Create the vector store
5. Update document status to "processed"
6. Set the cache flag

### Step 3: Verify Processing

After processing, check that everything worked:

```bash
# Check if vector store was created
dir vectorstore

# Should show files like:
# - index.faiss
# - index.pkl
```

### Step 4: Test the AI

Once the vector store is created, test the AI:

1. Ask a question about your business
2. The AI should now provide answers based on the document content
3. No more "no context" messages

## What the Processing Does

### 1. **Document Loading**
- Reads PDF, TXT, DOCX files
- Extracts text content
- Handles different file formats

### 2. **Text Chunking**
- Splits documents into smaller chunks (500 characters)
- Maintains context with overlap (50 characters)
- Creates searchable segments

### 3. **Vector Embeddings**
- Converts text chunks to vector embeddings
- Uses sentence-transformers model
- Enables similarity search

### 4. **Vector Store Creation**
- Stores embeddings in FAISS index
- Enables fast similarity search
- Allows AI to find relevant content

## Troubleshooting

### Issue: "No documents found in database"
**Solution**: Upload documents through Django admin first

### Issue: "File not found"
**Solution**: Check if document files exist in media directory

### Issue: "Failed to create vector store"
**Solution**: Check document format and content

### Issue: "No chunks created"
**Solution**: Document might be empty or in unsupported format

## Expected Results

After successful processing:

### Before Processing:
```
AI: "I can see that documents exist in the database, but they haven't been processed into the knowledge base yet..."
```

### After Processing:
```
AI: "Based on my records, I offer several key services that I'm really passionate about. Let me tell you about my pricing structure..."
```

## Manual Processing Steps

If the script doesn't work, you can process manually:

1. **Copy documents to knowledge base**:
   ```bash
   # Copy from media to knowledge base
   copy media\knowledge_base\* knowledge_base\
   ```

2. **Run ingest script**:
   ```bash
   python -c "from scribble.ingest import main; main()"
   ```

3. **Update cache**:
   ```bash
   python -c "from django.core.cache import cache; cache.set('DOCUMENTS_UPLOADED', True, timeout=None)"
   ```

## Admin Interface Processing

You can also process documents through the admin interface:

1. Go to Django admin (`/admin/`)
2. Navigate to "Knowledge documents"
3. Select documents to reprocess
4. Use "Reprocess selected documents" action

## Verification Commands

### Check Document Status:
```bash
python check_documents.py
```

### Check Vector Store:
```bash
dir vectorstore
```

### Test AI Response:
Ask the AI a question about your business content

## Next Steps

1. **Run the processing script** to create the vector store
2. **Test the AI** with questions about your business
3. **Upload more documents** through admin if needed
4. **Monitor performance** and adjust chunk sizes if needed

Once the vector store is created, the AI will be able to answer questions based on your document content instead of saying "no context". 