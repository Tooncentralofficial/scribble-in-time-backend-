from django.core.management.base import BaseCommand
from scribble.models import KnowledgeDocument

class Command(BaseCommand):
    help = 'List all documents in the database'

    def handle(self, *args, **options):
        documents = KnowledgeDocument.objects.all()
        if documents.exists():
            self.stdout.write(self.style.SUCCESS('Found documents:'))
            for doc in documents:
                self.stdout.write(f"- ID: {doc.id}, Title: {doc.title}, Uploaded: {doc.uploaded_at}")
                self.stdout.write(f"  File: {doc.file.path if doc.file else 'No file'}")
                self.stdout.write(f"  Processed: {doc.is_processed}")
        else:
            self.stdout.write(self.style.WARNING('No documents found in the database.'))
