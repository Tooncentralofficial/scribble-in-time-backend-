import time
import logging
from rest_framework.views import APIView

logger = logging.getLogger(__name__)
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.conf import settings
from .ai_service import AIService
from .models import Message, Conversation, KnowledgeDocument
from .serializers import MessageSerializer, DocumentSerializer
from .document_processor import DocumentProcessor
from rest_framework.parsers import MultiPartParser, FormParser

class ChatAPIHome(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({
            'status': 'success',
            'message': 'Chat API is running',
            'endpoints': {
                'send_message': '/api/chat/messages/send/',
                'get_messages': '/api/chat/messages/conversation/<user_id>/',
                'admin_send_message': '/api/chat/admin/send-message/'
            }
        }, status=status.HTTP_200_OK)


class DocumentUploadView(APIView):
    """Handle document uploads for the knowledge base"""
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        try:
            # Debug logging
            logger.info(f"Document upload request received")
            logger.info(f"Request FILES: {request.FILES}")
            logger.info(f"Request content type: {request.content_type}")
            
            file_obj = request.FILES.get('file')
            if not file_obj:
                logger.error("No file found in request.FILES")
                return Response(
                    {'error': 'No file provided'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get file extension
            file_ext = file_obj.name.split('.')[-1].lower()
            if file_ext not in ['pdf', 'txt', 'md', 'docx']:
                return Response(
                    {'error': 'Unsupported file type'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create document in database
            document = KnowledgeDocument.objects.create(
                file=file_obj,
                title=file_obj.name,
                file_type=file_ext,
                is_processed=False
            )
            
            # Process document in background
            import threading
            processor = DocumentProcessor()
            thread = threading.Thread(
                target=processor.process_document,
                args=(document,)
            )
            thread.daemon = True
            thread.start()
            
            # Also try to clean up any corrupted vector store files
            try:
                import os
                from pathlib import Path
                vectorstore_path = Path(__file__).resolve().parent.parent / "vectorstore"
                index_file = vectorstore_path / "index.faiss"
                pkl_file = vectorstore_path / "index.pkl"
                
                # If files exist but are empty, remove them
                if (index_file.exists() and index_file.stat().st_size == 0) or \
                   (pkl_file.exists() and pkl_file.stat().st_size == 0):
                    logger.warning("Found empty vector store files, removing them")
                    if index_file.exists() and index_file.stat().st_size == 0:
                        index_file.unlink()
                    if pkl_file.exists() and pkl_file.stat().st_size == 0:
                        pkl_file.unlink()
            except Exception as cleanup_error:
                logger.warning(f"Error during vector store cleanup: {str(cleanup_error)}")
            
            # Return immediate response
            return Response(
                {
                    'id': document.id,
                    'title': document.title,
                    'status': 'processing'
                },
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            logger.error(f"Error in document upload: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SendMessageView(APIView):
    authentication_classes = []  # Disable authentication
    permission_classes = [AllowAny]  # Explicitly allow any access

    def options(self, request, *args, **kwargs):
        # Handle preflight requests
        response = Response(status=status.HTTP_200_OK)
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-CSRFToken'
        response['Access-Control-Allow-Credentials'] = 'true'
        return response

    def post(self, request):
        # Bypass CSRF verification
        request._dont_enforce_csrf_checks = True
        
        # Set CORS headers
        response = Response()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-CSRFToken'
        
        user_id = request.data.get('user_id') or f'anonymous_{int(time.time())}'
        message_content = request.data.get('message')
        
        if not message_content:
            response.data = {'error': 'Message content is required'}
            response.status_code = status.HTTP_400_BAD_REQUEST
            return response
        
        try:
            # Get or create conversation without any authentication
            conversation, _ = Conversation.objects.get_or_create(
                user_id=user_id,
                defaults={'status': 'active'}
            )
            
            # Save user message
            message = Message.objects.create(
                conversation=conversation,
                content=message_content,
                sender='user',
                sender_username=user_id
            )
            
            # Get AI response - let the AIService handle document checking
            ai_response = AIService.get_ai_response(
                message_content,
                conversation_history=Message.objects.filter(conversation=conversation).order_by('created_at')
            )
            
            # Save AI response to the database
            ai_message = Message.objects.create(
                conversation=conversation,
                content=ai_response['message'],
                sender='ai',
                sender_username='ai_assistant'
            )
            
            response_data = {
                    'status': 'success',
                    'message': 'Message sent successfully',
                    'message_id': str(message.id),
                    'ai_response': {
                        'message': ai_response['message'],
                        'created_at': ai_response.get('timestamp', timezone.now().isoformat()),
                        'message_id': str(ai_message.id),
                        'model': ai_response.get('model', 'default'),
                        'needs_document': ai_response.get('needs_document', True)
                    }
                }
            
            # Set response data and status
            response.data = response_data
            response.status_code = status.HTTP_201_CREATED
            return response
            
        except Exception as e:
            response.data = {'error': str(e)}
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return response


class AdminMessageAPI(APIView):
    # Only allow admin users to access this endpoint
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        """Send a message as admin"""
        # Ensure user is authenticated and is staff/admin
        if not request.user.is_staff:
            return Response(
                {'error': 'Admin privileges required'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        user_id = request.data.get('user_id')
        message_content = request.data.get('message')
        
        if not user_id or not message_content:
            return Response(
                {'error': 'Both user_id and message are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get or create conversation
            conversation, _ = Conversation.objects.get_or_create(
                user_id=user_id,
                defaults={'status': 'active'}
            )
            
            # Save admin message
            message = Message.objects.create(
                conversation=conversation,
                content=message_content,
                sender='admin',
                sender_username=request.user.username or 'Admin'
            )
            
            # In a real implementation, you would notify the user via WebSocket here
            
            return Response({
                'status': 'success',
                'message': 'Admin message sent successfully',
                'message_id': str(message.id)
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetMessagesView(APIView):
    authentication_classes = []  # Disable authentication
    permission_classes = []  # No permissions required

    def options(self, request, *args, **kwargs):
        # Handle preflight requests
        response = Response(status=status.HTTP_200_OK)
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-CSRFToken'
        response['Access-Control-Allow-Credentials'] = 'true'
        return response

    def get(self, request, user_id):
        # Bypass CSRF verification
        request._dont_enforce_csrf_checks = True
        
        # Set up response with CORS headers
        response = Response()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-CSRFToken'
        
        try:
            conversation = Conversation.objects.filter(user_id=user_id).first()
            if not conversation:
                response.data = []
                response.status_code = status.HTTP_200_OK
                return response
                
            messages = Message.objects.filter(conversation=conversation).order_by('timestamp')
            serializer = MessageSerializer(messages, many=True)
            response.data = serializer.data
            response.status_code = status.HTTP_200_OK
            return response
            
        except Exception as e:
            response.data = {'error': str(e)}
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return response
