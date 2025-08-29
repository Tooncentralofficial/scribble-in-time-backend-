import os
import json
import requests
import logging
from django.conf import settings
from django.utils import timezone

# Set up logging
logger = logging.getLogger(__name__)

class AIService:
    @staticmethod
    def get_ai_response(user_message, conversation_history=None):
        """
        Get a response from the AI based on the user's message and conversation history
        using OpenRouter with document context.
        
        Args:
            user_message (str): The user's message
            conversation_history (QuerySet, optional): QuerySet of previous messages
            
        Returns:
            dict: AI response containing message and timestamp
        """
        # Default response if AI service is not properly configured
        default_response = {
            'message': "I'm currently unable to process your request. Please try again later.",
            'created_at': timezone.now().isoformat(),
            'model': getattr(settings, 'OPENROUTER_MODEL', 'default-model'),
            'needs_document': True,
            'error': 'Service configuration error'
        }
        
        # Import settings at the top level
        from django.conf import settings
        
        # Check if OpenRouter API key is configured
        if not hasattr(settings, 'OPENROUTER_API_KEY') or not settings.OPENROUTER_API_KEY:
            print("OpenRouter API key not configured")
            return default_response
        
        try:
            # Prepare the conversation history
            messages = []
            
            # System message for document-faithful responses
            system_message = getattr(settings, 'AI_SYSTEM_MESSAGE', 
                                  'You are Uche, the AI assistant for Scribble in Time. Your primary role is to provide information exactly as it appears in the provided documents.\n\n'
                                  'GUIDELINES FOR RESPONDING:\n                                  1. For factual questions, use the EXACT wording from the documents when possible\n'
                                  '2. For questions that require combining information, stay as close to the original text as possible\n'
                                  '3. Only improvise or rephrase if the question is clearly conversational (e.g., "How are you?", "Can you explain this in simpler terms?")\n'
                                  '4. If the exact information is not in the documents, say: "I don\'t have that information in my knowledge base."\n'
                                  '5. Maintain a professional but approachable tone\n\n'
                                  '6. When in doubt, prefer the exact wording from the documents over rephrasing')
            
            messages.append({"role": "system", "content": system_message})
            
            # Add conversation history if available
            if conversation_history:
                for msg in conversation_history:
                    role = "user" if msg.sender == 'user' else "assistant"
                    messages.append({"role": role, "content": msg.content})
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Get relevant document context from local FAISS vector store
            from langchain_community.embeddings import HuggingFaceEmbeddings
            from langchain_community.vectorstores import FAISS
            from django.conf import settings
            
            try:
                # Load the local FAISS vector store
                embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
                vectorstore = FAISS.load_local("vectorstore", embeddings, allow_dangerous_deserialization=True)
                
                # Get relevant document chunks with scores
                relevant_docs = vectorstore.similarity_search_with_score(user_message, k=5)
                
                # Filter out low relevance documents (score > 0.8)
                relevant_docs = [doc for doc, score in relevant_docs if score < 0.8]
                
                if not relevant_docs:
                    raise ValueError("No relevant documents found for the query.")
                
                # Prepare context from relevant documents with source information
                context_parts = []
                for i, doc in enumerate(relevant_docs, 1):
                    # Clean up the content
                    content = doc.page_content.strip()
                    if not content:
                        continue
                    context_parts.append(f"--- DOCUMENT EXCERPT {i} ---\n{content}")
                
                if not context_parts:
                    raise ValueError("No relevant content found in the documents.")
                
                context = "\n\n".join(context_parts)
                
                # Create a document-faithful prompt
                enhanced_message = f"""DOCUMENT EXCERPTS:
                {context}
                
                QUESTION: "{user_message}"
                
                INSTRUCTIONS:
                1. If this is a factual question, answer using the EXACT wording from the documents above.
                2. If you need to combine information, stay as close to the original text as possible.
                3. Only rephrase if the question is clearly conversational.
                4. If the information isn't in the documents, say: "I don't have that information in my knowledge base."
                
                ANSWER (use exact text when possible):"""
                
                # Update the last message with context
                messages[-1]['content'] = enhanced_message
                
            except Exception as e:
                print(f"Error retrieving document context: {str(e)}")
                return {
                    'message': "I'm having trouble accessing the knowledge base. Please try again later.",
                    'timestamp': timezone.now().isoformat(),
                    'model': settings.OPENROUTER_MODEL,
                    'needs_document': True
                }
            
            # Prepare the request payload
            payload = {
                "model": settings.OPENROUTER_MODEL,
                "messages": messages,
                "temperature": 0.3,  # Lower temperature for more focused responses
                "max_tokens": 2000,
                "stream": False
            }
            
            # Add strict system message to ensure document-based responses
            if len(messages) == 1:  # Only add the system message if it's a new conversation
                payload['system'] = """You are Uche, an AI assistant for Scribble in Time. 
                
                STRICT RULES:
                1. Your response MUST be based ONLY on the provided document context
                2. If the answer isn't in the context, say 'I don't have that information in my knowledge base.'
                3. Use the exact wording from the context when possible
                4. Be concise and professional in your responses
                5. Never make up information not in the context
                
                DOCUMENT CONTEXT HAS BEEN PROVIDED WITH THE USER'S QUESTION.
                
                Respond based on the document context provided."""
            
            # Log the request (without sensitive data)
            logger.info(f"Sending request to OpenRouter API with model: {payload.get('model')}")
            
            # Verify API key is available
            if not hasattr(settings, 'OPENROUTER_API_KEY') or not settings.OPENROUTER_API_KEY:
                raise ValueError("OpenRouter API key is not configured in settings")
                
            # Prepare headers
            headers = {
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            
            # Add optional headers if they exist in settings
            if hasattr(settings, 'OPENROUTER_HEADERS'):
                if "HTTP-Referer" in settings.OPENROUTER_HEADERS:
                    headers["HTTP-Referer"] = settings.OPENROUTER_HEADERS["HTTP-Referer"]
                if "X-Title" in settings.OPENROUTER_HEADERS:
                    headers["X-Title"] = settings.OPENROUTER_HEADERS["X-Title"]
            
            # Call OpenRouter API with timeout and better error handling
            try:
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60  # Increased timeout to 60 seconds
                )
                response.raise_for_status()
            except requests.exceptions.Timeout:
                raise Exception("The request to the AI service timed out. Please try again.")
            except requests.exceptions.RequestException as e:
                raise Exception(f"Error connecting to the AI service: {str(e)}")
            
            response.raise_for_status()
            response_data = response.json()
            
            # Get the AI's response
            ai_message = response_data['choices'][0]['message']['content'].strip()
            
            # Check if documents are available (check cache first, then database)
            try:
                from django.core.cache import cache
                from scribble.models import KnowledgeDocument
                
                documents_uploaded = cache.get('DOCUMENTS_UPLOADED', False)
                if not documents_uploaded and KnowledgeDocument.objects.filter(is_processed=True).exists():
                    cache.set('DOCUMENTS_UPLOADED', True, timeout=None)
                    documents_uploaded = True
                
                if not documents_uploaded:
                    return {
                        'message': "I can only answer questions based on the provided documents. Please upload relevant documents first.",
                        'timestamp': timezone.now().isoformat(),
                        'model': response_data.get('model', getattr(settings, 'OPENROUTER_MODEL', 'default-model')),
                        'needs_document': True
                    }
            except Exception as e:
                print(f"Error checking document status: {str(e)}")
                return {
                    'message': "I'm having trouble accessing the knowledge base. Please try again later.",
                    'timestamp': timezone.now().isoformat(),
                    'model': getattr(settings, 'OPENROUTER_MODEL', 'default-model'),
                    'needs_document': True
                }
                
            return {
                'message': ai_message,
                'timestamp': timezone.now().isoformat(),
                'model': response_data.get('model', settings.OPENROUTER_MODEL),
                'needs_document': False
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Request to OpenRouter API failed: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                error_msg += f"\nStatus Code: {e.response.status_code}"
                try:
                    error_details = e.response.json()
                    error_msg += f"\nError Details: {error_details}"
                except:
                    error_msg += f"\nResponse Text: {e.response.text}"
            print(error_msg)
            return {
                'message': "I'm having trouble connecting to the AI service. Please try again in a moment.",
                'timestamp': timezone.now().isoformat(),
                'model': getattr(settings, 'OPENROUTER_MODEL', 'default-model'),
                'error': error_msg[:200]  # Return first 200 chars of error for debugging
            }
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)} (Type: {type(e).__name__})"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return {
                'message': "I encountered an unexpected error. The developers have been notified.",
                'timestamp': timezone.now().isoformat(),
                'model': getattr(settings, 'OPENROUTER_MODEL', 'default-model'),
                'error': error_msg[:200]  # Return first 200 chars of error for debugging
            }
