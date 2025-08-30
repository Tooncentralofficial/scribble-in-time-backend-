from django.core.management.base import BaseCommand
from django.core.cache import cache
from scribble.ingest import main as process_documents
from scribble.models import KnowledgeDocument
import os
from pathlib import Path

class Command(BaseCommand):
    help = 'Process documents in the knowledge base and create vector store'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reprocessing even if documents are already processed',
        )

    def handle(self, *args, **options):
        self.stdout.write("Starting document processing...")
        
        # Check if knowledge base directory exists
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        knowledge_base_path = project_root / "knowledge_base"
        
        if not knowledge_base_path.exists():
            self.stdout.write(
                self.style.ERROR(f"Knowledge base directory not found at {knowledge_base_path}")
            )
            return
        
        # List files in knowledge base
        files = list(knowledge_base_path.glob("*"))
        if not files:
            self.stdout.write(
                self.style.WARNING("No files found in knowledge base directory")
            )
            return
        
        self.stdout.write(f"Found {len(files)} files in knowledge base:")
        for file in files:
            self.stdout.write(f"  - {file.name}")
        
        # Process documents
        try:
            success = process_documents()
            
            if success:
                # Update KnowledgeDocument records
                for file in files:
                    if file.is_file():
                        doc, created = KnowledgeDocument.objects.get_or_create(
                            file=f"knowledge_base/{file.name}",
                            defaults={
                                'title': file.stem,
                                'file_type': file.suffix[1:].lower(),
                                'is_processed': True,
                            }
                        )
                        if not created:
                            doc.is_processed = True
                            doc.processing_error = None
                            doc.save()
                
                # Update cache
                cache.set('DOCUMENTS_UPLOADED', True, timeout=None)
                
                self.stdout.write(
                    self.style.SUCCESS("Document processing completed successfully!")
                )
                self.stdout.write("Vector store has been created/updated.")
                self.stdout.write("AI can now use the knowledge base to answer questions.")
            else:
                self.stdout.write(
                    self.style.ERROR("Document processing failed!")
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error during document processing: {str(e)}")
            ) 