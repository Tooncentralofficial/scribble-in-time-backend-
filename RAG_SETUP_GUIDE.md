# RAG (Retrieval-Augmented Generation) Setup Guide

## Overview

The AI system uses a RAG (Retrieval-Augmented Generation) approach where:
1. **Admin uploads documents** through the Django admin interface
2. **Documents are automatically processed** and converted to vector embeddings
3. **Vector store is created** for fast similarity search
4. **AI uses the vector store** to retrieve relevant information when answering questions

## Current Issue

The AI is responding with "There is no relevant information in the context" because:
- Documents exist in the `knowledge_base/` directory
- But the vector store hasn't been created yet
- The automatic processing pipeline needs to be triggered

## Solution Steps

### Step 1: Process Existing Documents

Since there's already a document in the knowledge base, we need to process it:

```bash
# Option 1: Use the management command (if Python process is available)
python manage.py process_documents

# Option 2: Use the simple script
python process_docs.py

# Option 3: Manual processing
python -c "from scribble.ingest import main; main()"
```

### Step 2: Verify Vector Store Creation

After processing, check if the vector store was created:

```bash
dir vectorstore
```

You should see files like:
- `index.faiss` (vector index)
- `index.pkl` (metadata)

### Step 3: Test the AI

Once the vector store is created, the AI should be able to answer questions based on the uploaded documents.

## Automatic Processing Pipeline

### How It Works

1. **Admin Upload**: Admin uploads document through Django admin
2. **Automatic Processing**: The `KnowledgeDocumentAdmin.save_model()` method:
   - Copies the file to `knowledge_base/` directory
   - Calls the ingest module to process the document
   - Creates/updates the vector store
   - Marks the document as processed
   - Updates the cache

### Admin Interface

The admin interface now includes:
- **Document upload**: Upload PDF, TXT, MD, DOCX files
- **Processing status**: Shows if document is processed
- **Error tracking**: Shows processing errors if any
- **Reprocess action**: Manually reprocess documents

### File Structure

```
scribble-in-time-backend-/
├── knowledge_base/          # Documents uploaded by admin
│   └── Uche AI Full Training Data Set.pdf
├── vectorstore/             # Created after processing
│   ├── index.faiss
│   └── index.pkl
├── scribble/
│   ├── ingest.py           # Document processing logic
│   ├── admin.py            # Admin interface with auto-processing
│   └── models.py           # KnowledgeDocument model
└── chat/
    └── ai_service.py       # AI service using vector store
```

## Configuration

### Environment Variables

Make sure these are set in your environment:
- `OPENROUTER_API_KEY`: Your OpenRouter API key
- `SECRET_KEY`: Django secret key
- `DEBUG`: Set to `False` for production

### Vector Store Settings

The vector store uses:
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Chunk size**: 500 characters
- **Chunk overlap**: 50 characters
- **Similarity search**: Top 5 most relevant chunks

## Troubleshooting

### Issue: "No relevant information in context"

**Cause**: Vector store doesn't exist or is empty
**Solution**: Process documents using one of the methods above

### Issue: "Error processing document"

**Cause**: Document format not supported or processing error
**Solution**: 
1. Check document format (PDF, TXT, MD, DOCX supported)
2. Check admin interface for processing errors
3. Try reprocessing from admin

### Issue: Python process lock

**Cause**: Another Python process is running
**Solution**: 
1. Close any running Django development server
2. Wait a few minutes and try again
3. Restart your terminal/command prompt

### Issue: Memory errors during processing

**Cause**: Large documents or insufficient memory
**Solution**:
1. Split large documents into smaller files
2. Increase system memory
3. Use smaller chunk sizes in `ingest.py`

## Testing the RAG System

### 1. Upload a Document

1. Go to Django admin (`/admin/`)
2. Navigate to "Knowledge documents"
3. Click "Add knowledge document"
4. Upload a PDF or text file
5. Save - processing should start automatically

### 2. Test AI Responses

Once documents are processed, test with questions like:
- "What services do you offer?"
- "Tell me about your pricing"
- "What makes your business different?"

The AI should now provide specific answers based on the uploaded documents.

### 3. Verify Processing

Check the admin interface to see:
- Document status: "Processed" or "Not processed"
- Processing errors (if any)
- File information

## Advanced Features

### Memory Integration

The AI now uses:
- **Conversation memory**: Remembers previous interactions
- **Document context**: Uses uploaded documents as knowledge base
- **Confidence checking**: Refers to human contact when uncertain

### Adaptive Responses

The AI can:
- Provide brief answers for general questions
- Give detailed responses when asked to be "expansive"
- Use first-person communication as the business owner
- Refer to human contact when needed

## Deployment Notes

### Railway Deployment

For Railway deployment:
1. Documents should be uploaded through the admin interface
2. Processing happens automatically on upload
3. Vector store is created in the project directory
4. Cache is used to track document availability

### Local Development

For local development:
1. Use the management command to process existing documents
2. Monitor the admin interface for processing status
3. Check logs for any processing errors

## Next Steps

1. **Process the existing document** using one of the methods above
2. **Test the AI** with questions about the business
3. **Upload additional documents** through the admin interface
4. **Monitor performance** and adjust chunk sizes if needed

The RAG system is now fully configured and should provide accurate, document-based responses once the vector store is created. 