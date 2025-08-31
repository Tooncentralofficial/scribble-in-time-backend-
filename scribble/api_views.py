import os
import logging
from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from rest_framework.decorators import api_view

from .models import Conversation, Message, Document, AdminSettings, KnowledgeDocument, MemoirFormSubmission
from .serializers import (
    UserSerializer, ConversationSerializer, 
    MessageSerializer, DocumentSerializer, AdminSettingsSerializer,
    MessageCreateSerializer, MemoirFormSubmissionSerializer, MemoirFormSubmissionResponseSerializer
)

User = get_user_model()

class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_staff

class DashboardStatsView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Get conversation statistics
        total_conversations = Conversation.objects.count()
        active_conversations = Conversation.objects.filter(is_active=True).count()
        conversations_today = Conversation.objects.filter(
            created_at__date=timezone.now().date()
        ).count()
        
        # Get message statistics
        total_messages = Message.objects.count()
        messages_today = Message.objects.filter(
            created_at__date=timezone.now().date()
        ).count()
        
        # Get user statistics
        total_users = User.objects.count()
        new_users_today = User.objects.filter(
            date_joined__date=timezone.now().date()
        ).count()
        
        # Get recent conversations
        recent_conversations = Conversation.objects.order_by('-updated_at')[:5]
        
        data = {
            'conversations': {
                'total': total_conversations,
                'active': active_conversations,
                'today': conversations_today,
            },
            'messages': {
                'total': total_messages,
                'today': messages_today,
            },
            'users': {
                'total': total_users,
                'new_today': new_users_today,
            },
            'recent_conversations': ConversationSerializer(recent_conversations, many=True).data
        }
        
        return Response(data)

class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [AllowAny]  # Changed from IsAdminUser to AllowAny
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by user
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
            
        # Filter by status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
            
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            queryset = queryset.filter(
                created_at__date__range=[start_date, end_date]
            )
            
        return queryset.order_by('-updated_at')
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        conversation = self.get_object()
        messages = conversation.messages.all().order_by('created_at')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by conversation
        conversation_id = self.request.query_params.get('conversation_id')
        if conversation_id:
            queryset = queryset.filter(conversation_id=conversation_id)
            
        # Filter by sender
        sender = self.request.query_params.get('sender')
        if sender:
            queryset = queryset.filter(sender=sender)
            
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            queryset = queryset.filter(
                created_at__date__range=[start_date, end_date]
            )
            
        return queryset.order_by('-created_at')

class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all().order_by('-uploaded_at')
    serializer_class = DocumentSerializer
    permission_classes = [AllowAny]
    pagination_class = None  # Disable pagination for now to avoid ordering warning
    
    def create(self, request, *args, **kwargs):
        try:
            # Get the file
            if not request.FILES or 'file' not in request.FILES:
                return Response(
                    {'error': 'No file was submitted'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            uploaded_file = request.FILES['file']
            
            # Prepare data for serializer
            data = {
                'file': uploaded_file,
                'title': request.data.get('title') or os.path.splitext(uploaded_file.name)[0],
                'document_type': request.data.get('document_type', 'knowledge')
            }
            
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
                headers=headers
            )
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def perform_create(self, serializer):
        # Save without setting user to avoid authentication issues
        serializer.save()

class ToggleAIResponseView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request, pk):
        try:
            conversation = Conversation.objects.get(pk=pk)
            conversation.ai_enabled = not conversation.ai_enabled
            conversation.save()
            
            # Add a system message about the change
            Message.objects.create(
                conversation=conversation,
                sender='system',
                content=f'AI responses have been turned {"on" if conversation.ai_enabled else "off"} by admin.'
            )
            
            return Response({
                'status': 'success',
                'ai_enabled': conversation.ai_enabled
            })
        except Conversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found'},
                status=status.HTTP_404_NOT_FOUND
            )

class AdminReplyView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request, conversation_id):
        content = request.data.get('content')
        if not content:
            return Response(
                {'error': 'Content is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            conversation = Conversation.objects.get(pk=conversation_id)
            
            # Create admin message
            message = Message.objects.create(
                conversation=conversation,
                sender='admin',
                content=content,
                is_read=True
            )
            
            # Update conversation timestamp
            conversation.updated_at = timezone.now()
            conversation.save()
            
            # TODO: Send notification to user
            
            return Response(MessageSerializer(message).data)
            
        except Conversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found'},
                status=status.HTTP_404_NOT_FOUND
            )

import logging
logger = logging.getLogger(__name__)

class DocumentUploadView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        # Initialize document as None for cleanup in case of failure
        doc = None
        file_path = None
        
        try:
            # Validate request has files
            if not hasattr(request, 'FILES') or not request.FILES:
                return Response(
                    {'error': 'No file was submitted'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get and validate the file
            uploaded_file = request.FILES.get('file')
            if not uploaded_file:
                return Response(
                    {'error': 'No file was submitted'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate file type
            if not uploaded_file.name.lower().endswith(('.pdf', '.txt', '.md')):
                return Response(
                    {'error': 'Only PDF, TXT, and MD files are allowed'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create document record first (in unprocessed state)
            doc = KnowledgeDocument(
                file=uploaded_file,
                is_processed=False
            )
            doc.save()
            
            # Set the DOCUMENTS_UPLOADED flag in cache
            from django.core.cache import cache
            cache.set('DOCUMENTS_UPLOADED', True, timeout=None)  # No expiration
            
            # Ensure knowledge base directory exists
            os.makedirs('knowledge_base', exist_ok=True)
            file_path = os.path.join('knowledge_base', uploaded_file.name)
            
            # Save the file
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            
            # Process the document
            from .ingest import load_documents, chunk_documents, create_vector_store
            from django.conf import settings
            import shutil
            
            # Ensure knowledge_base directory exists
            os.makedirs('knowledge_base', exist_ok=True)
            
            # Clear any existing vector store to avoid conflicts
            if os.path.exists('vectorstore'):
                shutil.rmtree('vectorstore')
            
            # Load and process all documents
            logger.info("Loading and processing documents...")
            documents = load_documents('knowledge_base')
            
            if not documents:
                logger.error("No documents could be loaded from knowledge_base directory")
                doc.delete()
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
                return Response(
                    {'error': 'Failed to load any documents'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
            # Chunk and create vector store
            logger.info(f"Processing {len(documents)} documents...")
            chunks = chunk_documents(documents)
            logger.info(f"Created {len(chunks)} chunks from documents")
            
            try:
                vectorstore = create_vector_store(chunks)
                logger.info(f"Created vector store with {vectorstore.index.ntotal} vectors")
            except Exception as e:
                logger.error(f"Error creating vector store: {str(e)}")
                doc.delete()
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
                return Response(
                    {'error': 'Failed to create vector store'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Mark document as processed
            doc.is_processed = True
            doc.save()
            
            # Update cache
            from django.core.cache import cache
            cache.set('DOCUMENTS_UPLOADED', True, timeout=None)
            
            # Ensure DOCUMENTS_UPLOADED flag is set in cache if we have documents
            if documents:
                cache.set('DOCUMENTS_UPLOADED', True, timeout=None)  # No expiration
            
            if not documents:
                error_msg = "No valid content could be extracted from the document. " \
                          "The file might be empty, corrupted, or in an unsupported format."
                logger.error(error_msg)
                raise Exception(error_msg)
            
            logger.info(f"Successfully loaded {len(documents)} document(s)")
            
            # Chunk the documents
            logger.info("Chunking document content...")
            chunks = chunk_documents(documents)
            
            if not chunks:
                error_msg = "Failed to create document chunks. The content might be too short or malformed."
                logger.error(error_msg)
                raise Exception(error_msg)
                
            logger.info(f"Created {len(chunks)} chunks from the document")
            
            # Create or update the vector store
            logger.info("Updating vector store...")
            vectorstore = create_or_update_vector_store(chunks)
            
            if vectorstore is None:
                error_msg = "Failed to create/update vector store. Please check the logs for more details."
                logger.error(error_msg)
                raise Exception(error_msg)
                
            logger.info("Successfully updated vector store")
            
            # Update document status to processed
            doc.is_processed = True
            doc.save()
            
            # Verify the document was actually processed
            if not doc.is_processed:
                raise Exception("Document processing verification failed")
            
            return Response({
                'status': 'success',
                'message': 'Document uploaded and processed successfully',
                'document': {
                    'id': doc.id,
                    'file': doc.file.name,
                    'uploaded_at': doc.uploaded_at.isoformat(),
                    'is_processed': doc.is_processed,
                    'file_size': doc.file.size if doc.file else 0
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            # Clean up in case of failure
            if doc and doc.id:
                try:
                    if doc.file:
                        doc.file.delete()
                    doc.delete()
                except Exception as cleanup_error:
                    logger.error(f"Error during cleanup: {str(cleanup_error)}")
            
            # Clean up the saved file if it exists
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as file_error:
                    logger.error(f"Error removing file {file_path}: {str(file_error)}")
            
            logger.error(f"Error in document upload: {str(e)}", exc_info=True)
            return Response(
                {
                    'error': 'Failed to process document',
                    'details': str(e),
                    'document_id': str(doc.id) if doc and hasattr(doc, 'id') else None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UserListView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

class UserDetailView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
            serializer = UserSerializer(user)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

class DocumentDeleteView(APIView):
    permission_classes = [AllowAny]
    
    def delete(self, request, *args, **kwargs):
        try:
            # Get the document (there should be only one)
            document = Document.objects.first()
            
            if not document:
                return Response(
                    {'status': 'error', 'message': 'No document found to delete'},
                    status=status.HTTP_404_NOT_FOUND
                )
                
            # Delete the file from storage
            if document.file:
                if os.path.exists(document.file.path):
                    os.remove(document.file.path)
            
            # Clear the knowledge base directory
            knowledge_base_dir = os.path.join('knowledge_base')
            if os.path.exists(knowledge_base_dir):
                for filename in os.listdir(knowledge_base_dir):
                    file_path = os.path.join(knowledge_base_dir, filename)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                    except Exception as e:
                        logger.error(f'Error deleting file {file_path}: {str(e)}')
            
            # Delete the document record
            document.delete()
            
            # Clear the vector store
            vectorstore_path = 'vectorstore'
            if os.path.exists(vectorstore_path):
                for filename in os.listdir(vectorstore_path):
                    file_path = os.path.join(vectorstore_path, filename)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                    except Exception as e:
                        logger.error(f'Error deleting vector store file {file_path}: {str(e)}')
            
            return Response({
                'status': 'success',
                'message': 'Document and its vector store have been deleted successfully'
            })
            
        except Exception as e:
            logger.error(f'Error deleting document: {str(e)}')
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AdminSettingsView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        settings, created = AdminSettings.objects.get_or_create(pk=1)
        serializer = AdminSettingsSerializer(settings)
        return Response(serializer.data)
        
    def put(self, request):
        settings = AdminSettings.objects.get(pk=1)
        serializer = AdminSettingsSerializer(settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def submit_memoir_form(request):
    """
    Submit a memoir form with personal and memoir details
    
    Expected payload:
    {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone_number": "+1234567890",
        "gender": "male",
        "theme": "Overcoming adversity",
        "subject": "My journey through cancer",
        "main_themes": "Resilience, family support, medical journey",
        "key_life_events": "Diagnosis, treatment, recovery, new perspective",
        "audience": "family_friends"
    }
    """
    try:
        # Validate the incoming data
        serializer = MemoirFormSubmissionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Validation failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Save the memoir form submission
        memoir_submission = serializer.save()
        
        # Create response data
        response_serializer = MemoirFormSubmissionResponseSerializer(memoir_submission)
        
        # Log the submission
        logger.info(f"New memoir form submission received from {memoir_submission.email}")
        
        return Response({
            'success': True,
            'message': 'Memoir form submitted successfully! We will review your submission and get back to you soon.',
            'data': response_serializer.data,
            'submission_id': memoir_submission.id
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error processing memoir form submission: {str(e)}")
        
        # Check if it's a missing table error
        if "no such table" in str(e).lower() and "memoirformsubmission" in str(e).lower():
            return Response({
                'success': False,
                'message': 'The system is still initializing. Please try again in a few moments.',
                'error': 'Database table not ready yet'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        return Response({
            'success': False,
            'message': 'An error occurred while processing your submission. Please try again.',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_memoir_form_submissions(request):
    """
    Get all memoir form submissions (admin endpoint)
    
    Query parameters:
    - page: Page number for pagination
    - page_size: Number of items per page (default: 20)
    - search: Search term for filtering by name, email, or theme
    - audience: Filter by audience type
    - is_processed: Filter by processing status (true/false)
    - date_from: Filter submissions from this date (YYYY-MM-DD)
    - date_to: Filter submissions until this date (YYYY-MM-DD)
    """
    try:
        # Get query parameters
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 20)), 100)  # Max 100 per page
        search = request.GET.get('search', '').strip()
        audience = request.GET.get('audience', '').strip()
        is_processed = request.GET.get('is_processed', '').strip()
        date_from = request.GET.get('date_from', '').strip()
        date_to = request.GET.get('date_to', '').strip()
        
        # Start with all submissions
        queryset = MemoirFormSubmission.objects.all()
        
        # Apply filters
        if search:
            queryset = queryset.filter(
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search) |
                models.Q(email__icontains=search) |
                models.Q(theme__icontains=search) |
                models.Q(subject__icontains=search)
            )
        
        if audience:
            queryset = queryset.filter(audience=audience)
        
        if is_processed:
            if is_processed.lower() == 'true':
                queryset = queryset.filter(is_processed=True)
            elif is_processed.lower() == 'false':
                queryset = queryset.filter(is_processed=False)
        
        if date_from:
            try:
                from datetime import datetime
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(submitted_at__date__gte=date_from_obj)
            except ValueError:
                pass
        
        if date_to:
            try:
                from datetime import datetime
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(submitted_at__date__lte=date_to_obj)
            except ValueError:
                pass
        
        # Paginate results
        paginator = Paginator(queryset, page_size)
        try:
            submissions_page = paginator.page(page)
        except (EmptyPage, InvalidPage):
            submissions_page = paginator.page(paginator.num_pages)
        
        # Serialize the data
        serializer = MemoirFormSubmissionResponseSerializer(submissions_page, many=True)
        
        # Prepare response data
        response_data = {
            'success': True,
            'data': serializer.data,
            'pagination': {
                'current_page': submissions_page.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': submissions_page.has_next(),
                'has_previous': submissions_page.has_previous(),
                'page_size': page_size
            },
            'filters': {
                'search': search,
                'audience': audience,
                'is_processed': is_processed,
                'date_from': date_from,
                'date_to': date_to
            }
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error fetching memoir form submissions: {str(e)}")
        
        # Check if it's a missing table error
        if "no such table" in str(e).lower() and "memoirformsubmission" in str(e).lower():
            return Response({
                'success': False,
                'message': 'The system is still initializing. Please try again in a few moments.',
                'error': 'Database table not ready yet'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        return Response({
            'success': False,
            'message': 'An error occurred while fetching submissions.',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_memoir_form_options(request):
    """
    Get available options for the memoir form (gender choices, audience choices, etc.)
    """
    try:
        options = {
            'gender_choices': [
                {'value': choice[0], 'label': choice[1]} 
                for choice in MemoirFormSubmission.GENDER_CHOICES
            ],
            'audience_choices': [
                {'value': choice[0], 'label': choice[1]} 
                for choice in MemoirFormSubmission.AUDIENCE_CHOICES
            ],
            'form_fields': {
                'personal_info': [
                    'first_name', 'last_name', 'email', 'phone_number', 'gender'
                ],
                'memoir_details': [
                    'theme', 'subject', 'main_themes', 'key_life_events', 'audience'
                ]
            }
        }
        
        return Response({
            'success': True,
            'data': options
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting memoir form options: {str(e)}")
        return Response({
            'success': False,
            'message': 'An error occurred while fetching form options.',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
