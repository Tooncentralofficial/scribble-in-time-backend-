import logging
from celery import shared_task
from .models import KnowledgeDocument
from .document_processor import DocumentProcessor

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def process_document_async(self, document_id):
    """
    Asynchronous task to process a document and update the vector store
    """
    try:
        document = KnowledgeDocument.objects.get(id=document_id)
        
        # Update status to processing
        document.status = 'processing'
        document.save()
        
        # Process the document
        processor = DocumentProcessor()
        success = processor.process_document(document)
        
        # Update status based on processing result
        if success:
            document.status = 'processed'
            document.save()
            logger.info(f"Successfully processed document ID: {document_id}")
            return {
                'status': 'success',
                'document_id': document_id,
                'message': 'Document processed successfully'
            }
        else:
            document.status = 'failed'
            document.save()
            error_msg = f"Failed to process document ID: {document_id}"
            logger.error(error_msg)
            return {
                'status': 'error',
                'document_id': document_id,
                'message': error_msg
            }
            
    except KnowledgeDocument.DoesNotExist:
        error_msg = f"Document with ID {document_id} does not exist"
        logger.error(error_msg)
        return {
            'status': 'error',
            'document_id': document_id,
            'message': error_msg
        }
        
    except Exception as e:
        error_msg = f"Error processing document {document_id}: {str(e)}"
        logger.error(error_msg)
        
        # Update document status
        try:
            document = KnowledgeDocument.objects.get(id=document_id)
            document.status = 'failed'
            document.processing_error = error_msg
            document.save()
        except:
            pass
            
        # Retry the task with exponential backoff
        raise self.retry(exc=e, countdown=60 * self.request.retries)
