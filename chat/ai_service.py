import os
import json
import requests
import logging
from django.conf import settings
from django.utils import timezone
from scribble.memory_system import MemorySystem

# Set up logging
logger = logging.getLogger(__name__)

class AIService:
    @staticmethod
    def get_ai_response(user_message, conversation_history=None, session_id=None):
        """
        Get a response from the AI based on the user's message and conversation history
        using OpenRouter with document context and memory system.
        
        Args:
            user_message (str): The user's message
            conversation_history (QuerySet, optional): QuerySet of previous messages
            session_id (str, optional): Session ID for memory management
            
        Returns:
            dict: AI response containing message and timestamp
        """
        # Initialize memory system
        memory_system = MemorySystem(session_id)
        
        # Add user message to memory
        memory_system.add_user_message(user_message)
        
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
            
            # System message for personalized, document-based responses
            system_message = getattr(settings, 'AI_SYSTEM_MESSAGE', 
                                  'You are Uche, the owner and founder of Scribble in Time. You\'re speaking directly to your customers and potential clients.\n\n'
                                  'PERSONALITY & COMMUNICATION STYLE:\n'
                                  '- Speak as yourself (the business owner), not in third person\n'
                                  '- Be warm, personal, and conversational - like you\'re talking to a friend\n'
                                  '- Show genuine enthusiasm for your business and services\n'
                                  '- Use "I", "my", "we" - make it feel like a real conversation with the business owner\n\n'
                                  'RESPONSE GUIDELINES:\n'
                                  '- Base your answers on the provided documents, but speak naturally and conversationally\n'
                                  '- If someone asks for more details or wants you to be "expansive", provide comprehensive, detailed responses\n'
                                  '- For general questions, start with a brief answer but offer to elaborate if they\'d like more details\n'
                                  '- Never give generic, generalized answers - always be specific and personal\n'
                                  '- If you don\'t have information in the documents, say "I don\'t have that specific information in my records, but I\'d be happy to discuss it further with you"')
            
            messages.append({"role": "system", "content": system_message})
            
            # Add conversation history from both database and memory system
            if conversation_history:
                for msg in conversation_history:
                    role = "user" if msg.sender == 'user' else "assistant"
                    messages.append({"role": role, "content": msg.content})
            
            # Add memory context
            memory_context = memory_system.get_conversation_context()
            if memory_context:
                # Add memory context after system message but before conversation history
                messages.extend(memory_context[1:])  # Skip the system message as we have our own
            
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
                
                # Check if user wants an expansive response
                wants_expansive = any(word in user_message.lower() for word in [
                    'expansive', 'detailed', 'comprehensive', 'more details', 'explain more',
                    'tell me more', 'elaborate', 'in depth', 'thorough', 'complete'
                ])
                
                # Create a personalized, adaptive prompt with strong document emphasis
                enhanced_message = f"""DOCUMENT EXCERPTS FROM MY BUSINESS RECORDS:
                {context}
                
                CUSTOMER QUESTION: "{user_message}"
                
                RESPONSE INSTRUCTIONS:
                1. Answer as Uche, the business owner, speaking directly to the customer
                2. ALWAYS use the information from my documents above as your primary source
                3. Reference conversation memory for context when relevant
                4. {'Provide a comprehensive, detailed response since they asked for more information' if wants_expansive else 'Start with a clear answer, but offer to provide more details if they\'d like'}
                5. If the information isn't in my documents, say: "I don't have that specific information in my records, but I'd be happy to discuss it further with you"
                6. Be specific and personal - avoid generic answers
                7. Use "I", "my", "we" - speak as the business owner
                8. Be confident when you have information from your documents
                
                MY RESPONSE (based on my documents and memory):"""
                
                # Update the last message with context
                messages[-1]['content'] = enhanced_message
                
            except Exception as e:
                print(f"Error retrieving document context: {str(e)}")
                return {
                    'message': "I'm having trouble accessing my business records right now. Please try again in a moment, and I'll be happy to help you with any questions about my services.",
                    'timestamp': timezone.now().isoformat(),
                    'model': settings.OPENROUTER_MODEL,
                    'needs_document': True
                }
            
            # Prepare the request payload with adaptive settings
            payload = {
                "model": settings.OPENROUTER_MODEL,
                "messages": messages,
                "temperature": 0.7 if wants_expansive else 0.5,  # Higher temperature for more natural, expansive responses
                "max_tokens": 4000 if wants_expansive else 2000,  # More tokens for detailed responses
                "stream": False
            }
            
            # Add personalized system message for new conversations
            if len(messages) == 1:  # Only add the system message if it's a new conversation
                payload['system'] = """You are Uche, the owner and founder of Scribble in Time. You're speaking directly to your customers and potential clients.

PERSONALITY & COMMUNICATION STYLE:
- Speak as yourself (the business owner), not in third person
- Be warm, personal, and conversational - like you're talking to a friend
- Show genuine enthusiasm for your business and services
- Use "I", "my", "we" - make it feel like a real conversation with the business owner

RESPONSE GUIDELINES:
- ALWAYS use the provided document context as your primary source of information
- Use conversation memory to provide context-aware, personalized responses
- If someone asks for more details or wants you to be "expansive", provide comprehensive, detailed responses
- For general questions, start with a brief answer but offer to elaborate if they'd like more details
- Never give generic, generalized answers - always be specific and personal
- If you don't have information in the context, say "I don't have that specific information in my records, but I'd be happy to discuss it further with you"

DOCUMENT CONTEXT AND MEMORY HAVE BEEN PROVIDED WITH THE CUSTOMER'S QUESTION.
Respond as Uche, the business owner, using the information from your documents and memory."""
            
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
            
            # Check confidence indicators in the response
            confidence_indicators = [
                "I don't have that information",
                "I don't know",
                "I'm not sure",
                "I can't find",
                "I don't have that specific information",
                "I'm unable to",
                "I don't have access to",
                "I don't have details about",
                "I don't have records of",
                "I don't have information about"
            ]
            
            # Check if response indicates low confidence
            low_confidence = any(indicator.lower() in ai_message.lower() for indicator in confidence_indicators)
            
            # Add referral message if confidence is low
            if low_confidence:
                referral_message = f"\n\nFor more detailed information or clarification, please feel free to contact me directly at contact.ascribbleintime@gmail.com. I'd be happy to discuss this with you personally and provide any additional details you need."
                ai_message += referral_message
            
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
                        'message': "I'd love to help you with information about my business, but I need to have my documents uploaded first. Once that's done, I'll be able to answer your questions based on my records.",
                        'timestamp': timezone.now().isoformat(),
                        'model': response_data.get('model', getattr(settings, 'OPENROUTER_MODEL', 'default-model')),
                        'needs_document': True
                    }
            except Exception as e:
                print(f"Error checking document status: {str(e)}")
                return {
                    'message': "I'm having trouble accessing my business records right now. Please try again in a moment, and I'll be happy to help you with any questions about my services.",
                    'timestamp': timezone.now().isoformat(),
                    'model': getattr(settings, 'OPENROUTER_MODEL', 'default-model'),
                    'needs_document': True
                }
                
            # Add AI response to memory
            memory_system.add_assistant_message(ai_message)
            
            return {
                'message': ai_message,
                'timestamp': timezone.now().isoformat(),
                'model': response_data.get('model', settings.OPENROUTER_MODEL),
                'needs_document': False,
                'confidence': 'low' if low_confidence else 'high',
                'session_id': memory_system.session_id
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
