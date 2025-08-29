import json
import os
import logging

# Set up logging
logger = logging.getLogger(__name__)
from django.http import JsonResponse, HttpRequest
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from .ingest import load_documents, chunk_documents, create_or_update_vector_store
from .models import KnowledgeDocument, Conversation, Message
from .llm_utils import get_chat_completion
from .memory_system import MemorySystem
from dotenv import load_dotenv
from pathlib import Path

# Get the project root directory (where manage.py is located)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Configuration
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
VECTOR_STORE_PATH = str(PROJECT_ROOT / "vectorstore")

load_dotenv()

# Initialize embeddings as None - will be loaded when needed
embeddings = None

# Ensure vector store directory exists
os.makedirs(VECTOR_STORE_PATH, exist_ok=True)

# Initialize vector store as None - it will be loaded when needed
vectorstore = None

def get_embeddings():
    global embeddings
    if embeddings is None:
        embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)
    return embeddings

def get_vector_store():
    """Lazily load the vector store when needed"""
    global vectorstore
    if vectorstore is not None:
        return vectorstore
        
    # Get embeddings (will be loaded if not already)
    embeddings = get_embeddings()
    
    # Check if vector store exists and has the required files
    if os.path.exists(VECTOR_STORE_PATH):
        required_files = ['index.faiss', 'index.pkl']
        has_all_files = all(os.path.exists(os.path.join(VECTOR_STORE_PATH, f)) for f in required_files)
        
        if has_all_files:
            try:
                vectorstore = FAISS.load_local(
                    VECTOR_STORE_PATH,
                    embeddings,
                    allow_dangerous_deserialization=True
                )
                return vectorstore
            except Exception as e:
                print(f"Error loading vector store: {e}")
    
    # If we get here, either the vector store doesn't exist or failed to load
    # Create a new, empty vector store
    vectorstore = FAISS.from_texts(
        ["Initial document"],  # Add an initial document
        embedding=embeddings
    )
    vectorstore.save_local(VECTOR_STORE_PATH)
    return vectorstore

def get_memory_system(request: HttpRequest) -> MemorySystem:
    """Get or create memory system for the current session"""
    if not hasattr(request, 'memory_system'):
        session_id = request.session.session_key or request.session.create()
        request.memory_system = MemorySystem(session_id=session_id)
    return request.memory_system

@csrf_exempt
def upload_document(request):
    if request.method != 'POST':
        return JsonResponse({
            "status": "error",
            "error": "Only POST method is allowed"
        }, status=405)

    try:
        if 'file' not in request.FILES:
            return JsonResponse({
                'status': 'error',
                'error': 'No file provided'
            }, status=400)
        
        uploaded_file = request.FILES['file']
        
        # Check file type
        if not uploaded_file.name.lower().endswith(('.pdf', '.txt', '.md')):
            return JsonResponse({
                'status': 'error',
                'error': 'Only PDF, TXT, and MD files are allowed'
            }, status=400)
        
        # Clear existing documents and vector store
        KnowledgeDocument.objects.all().delete()
        if os.path.exists('knowledge_base'):
            for file in os.listdir('knowledge_base'):
                try:
                    os.remove(os.path.join('knowledge_base', file))
                except Exception as e:
                    logger.error(f"Error deleting file {file}: {str(e)}")
        
        # Save the new file to the knowledge base
        os.makedirs('knowledge_base', exist_ok=True)
        file_path = os.path.join('knowledge_base', uploaded_file.name)
        
        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        
        # Process the document
        from .ingest import load_documents, chunk_documents, create_or_update_vector_store
        
        # Load and process the document
        documents = load_documents('knowledge_base')
        chunks = chunk_documents(documents)
        
        # Create or update the vector store
        vectorstore = create_or_update_vector_store(chunks)
        
        # Save document info to the database
        doc = KnowledgeDocument(
            title=uploaded_file.name,
            file=uploaded_file,
            is_processed=True
        )
        doc.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Document uploaded and processed successfully',
            'document': {
                'id': doc.id,
                'title': doc.title,
                'uploaded_at': doc.uploaded_at.isoformat(),
                'is_processed': doc.is_processed
            }
        })
        
    except Exception as e:
        logger.error(f"Error in upload_document: {str(e)}")
        return JsonResponse({
            "status": "error",
            "error": str(e)
        }, status=500)
            
    return JsonResponse({
        "status": "error",
        "error": "Invalid request or no file provided"
    }, status=400)

from django.views.decorators.http import require_http_methods
from django.views import View
from django.http import JsonResponse
from .decorators import bypass_csrf_for_api
import json

@bypass_csrf_for_api
class ChatView(View):
    def dispatch(self, request, *args, **kwargs):
        # Handle OPTIONS method for CORS preflight
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()
            conversation_id = data.get('conversation_id')
            is_admin_reply = data.get('is_admin_reply', False)
            
            if not user_message:
                return JsonResponse({'error': 'Message is required'}, status=400)
            
            # Create or get conversation
            if conversation_id:
                try:
                    # For existing conversations, just get by ID
                    conversation = Conversation.objects.get(id=conversation_id)
                except (Conversation.DoesNotExist, ValueError):
                    return JsonResponse({'error': 'Invalid conversation ID'}, status=400)
            else:
                # For new conversations, create with session key or IP as fallback
                session_key = None
                if hasattr(request, 'session') and request.session.session_key:
                    session_key = request.session.session_key
                else:
                    # Generate a unique identifier from IP and timestamp if no session
                    ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
                    import time
                    session_key = f'anon_{ip}_{int(time.time())}'
                
                conversation = Conversation.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    session_key=session_key,
                    status='pending_ai'  # New conversation starts with AI response
                )
            
            # Save user message
            user_msg = Message.objects.create(
                conversation=conversation,
                content=user_message,
                sender='user'
            )
            
            # Check if this is an admin reply
            is_admin = hasattr(request, 'user') and request.user.is_authenticated and request.user.is_staff
            if is_admin_reply and is_admin:
                # Admin is replying, no need for AI response
                conversation.status = 'admin_responded'
                conversation.save()
                
                # Just return the user message for the admin to see
                return JsonResponse({
                    'status': 'awaiting_admin_response',
                    'message': 'Your message has been received and will be reviewed by our team.',
                    'conversation_id': conversation.id
                })
            
            # If conversation is waiting for admin, don't generate AI response
            if conversation.status == 'awaiting_admin':
                return JsonResponse({
                    'status': 'awaiting_admin_response',
                    'message': 'Your previous message is being reviewed by our team. Please wait for a response.',
                    'conversation_id': conversation.id
                })
            
            # Get AI response using the vector store
            from .llm_utils import get_chat_completion
            
            # Try to get the vector store
            vectorstore = get_vector_store()
            
            if vectorstore is None:
                # Check if knowledge base directory exists and has files
                kb_has_docs = os.path.exists('knowledge_base') and any(
                    f.endswith(('.pdf', '.txt', '.md')) 
                    for f in os.listdir('knowledge_base')
                )
                
                if kb_has_docs:
                    ai_response = (
                        "I'm still processing your documents. This may take a moment. "
                        "Please try again in a few seconds."
                    )
                else:
                    ai_response = (
                        "I'm not ready to answer questions yet. "
                        "Please upload some documents first using the upload form. "
                        "I can process PDF, TXT, and MD files."
                    )
            else:
                try:
                    # Get or create memory system for this conversation
                    memory_system = get_memory_system(request)
                    
                    # Get relevant context from documents using RAG
                    vector_store = get_vector_store()
                    try:
                        # Search for relevant document chunks
                        docs = vector_store.similarity_search(user_message, k=3)
                        
                        # Prepare context with source information
                        context_parts = []
                        for i, doc in enumerate(docs, 1):
                            source = getattr(doc, 'metadata', {}).get('source', 'document')
                            context_parts.append(f"--- Source {i} ({source}) ---\n{doc.page_content}")
                        
                        context = "\n\n".join(context_parts)
                        
                        # System prompt for the AI with RAG instructions
                        system_prompt = """You are Uche, the AI assistant for Scribble in Time. Your responses should be:
                        - Based SOLELY on the provided context from uploaded documents
                        - Direct and to the point (max 3 sentences)
                        - Professional and helpful
                        - If the answer isn't in the context, say so and suggest contacting support
                        
                        Your response must be a JSON object with these fields:
                        - response: Your answer based on the context
                        - needs_admin_review: true if you're unsure or the question is complex
                        - confidence: 0.0 to 1.0 based on how well the context answers the question
                        
                        Example response:
                        {
                            "response": "Based on our documents, we offer 24/7 support with a 4-hour response time.",
                            "needs_admin_review": false,
                            "confidence": 0.9
                        }
                        """
                        
                        messages = [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"CONTEXT FROM DOCUMENTS:\n{context}\n\nQUESTION: {user_message}\n\nAnswer based ONLY on the context above. If the answer isn't there, say so."}
                        ]
                    except Exception as e:
                        logger.error(f"Error retrieving document context: {str(e)}")
                        return JsonResponse({
                            'error': 'Error retrieving document context. Please try again.',
                            'status': 'error'
                        }, status=500)
                    
                    # Use the synchronous version of get_chat_completion
                    from .llm_utils import get_chat_completion_sync
                    response = get_chat_completion_sync(messages, response_format={ "type": "json_object" })
                    
                    if response['success']:
                        try:
                            # Parse the JSON response
                            ai_data = json.loads(response['content'])
                            ai_response = ai_data.get('response', 'I apologize, but I encountered an error processing your request.')
                            needs_admin_review = ai_data.get('needs_admin_review', False)
                            confidence = ai_data.get('confidence', 0.0)
                            
                            # Update conversation status if admin review is needed
                            if needs_admin_review or confidence < 0.5:  # Threshold for admin review
                                conversation.status = 'awaiting_admin'
                                conversation.save()
                                ai_response += "\n\n[Your question has been escalated to our support team for further assistance.]"
                            
                        except json.JSONDecodeError:
                            # Fallback if response is not valid JSON
                            ai_response = response['content']
                    else:
                        ai_response = "I'm having trouble generating a response right now. Please try again in a moment."
                    
                except Exception as e:
                    import traceback
                    logger.error(f"Error in chat view: {str(e)}\n{traceback.format_exc()}")
                    ai_response = "I encountered an error while processing your request. Please try again."
            
            # Update memory system
            memory_system = get_memory_system(request)
            memory_system.add_episodic_memory('user', user_message)
            
            # Save AI response if we have one
            if 'ai_response' in locals():
                memory_system.add_episodic_memory('assistant', ai_response)
                
                # Save AI response to database
                Message.objects.create(
                    conversation=conversation,
                    content=ai_response,
                    sender='ai'
                )
            
            # Prepare response data
            response_data = {
                'status': 'success',
                'response': ai_response if 'ai_response' in locals() else None,
                'conversation_id': conversation.id,
                'conversation_status': conversation.status
            }
            
            # If waiting for admin, add appropriate message
            if conversation.status == 'awaiting_admin':
                response_data['message'] = 'Your message has been escalated to our support team.'
            
            return JsonResponse(response_data)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
            
            response = JsonResponse(response_data)
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Allow-Headers'] = 'Content-Type, X-CSRFToken, X-Requested-With'
            return response
            
        except Exception as e:
            response = JsonResponse({"error": str(e)}, status=500)
            response['Access-Control-Allow-Origin'] = '*'
            return response

# Replace the old chat function with the class-based view
chat = ChatView.as_view()

def chat_page(request):
    return render(request, 'ai_agent/chat.html')

class AdminDashboardView(TemplateView):
    template_name = 'admin_dashboard/dashboard.html'
    
    @method_decorator(staff_member_required(login_url='/admin/login/'))
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Admin Dashboard'
        context['site_header'] = 'Scribble in Time Admin'
        context['site_title'] = 'Scribble in Time'
        context['user'] = self.request.user
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Add some basic statistics
        context.update({
            'total_users': User.objects.count(),
            'total_staff': User.objects.filter(is_staff=True).count(),
            'total_superusers': User.objects.filter(is_superuser=True).count(),
        })
        return context