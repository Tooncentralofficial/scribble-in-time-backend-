from openai import OpenAI
from django.conf import settings
import logging
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio

logger = logging.getLogger(__name__)

# Define models in order of preference with their configurations
MODEL_PRIORITY = [
    {
        'name': 'meta-llama/llama-3.2-3b-instruct',
        'config': {
            'temperature': 0.7,
            'max_tokens': 1000,
            'timeout': 10  # seconds
        }
    },
    {
        'name': 'mistralai/mistral-7b-instruct:free',
        'config': {
            'temperature': 0.8,
            'max_tokens': 1000,
            'timeout': 15
        }
    },
    {
        'name': 'meta-llama/llama-3.3-70b-instruct:free',
        'config': {
            'temperature': 0.7,
            'max_tokens': 1000,
            'timeout': 20
        }
    },
    # Fallback free models
    {
        'name': 'gryphe/mythomax-l2-13b:free',
        'config': {
            'temperature': 0.8,
            'max_tokens': 1000,
            'timeout': 15
        }
    },
    {
        'name': 'huggingfaceh4/zephyr-7b-beta:free',
        'config': {
            'temperature': 0.7,
            'max_tokens': 1000,
            'timeout': 15
        }
    }
]

def get_openrouter_client():
    """Initialize and return an OpenAI client configured for OpenRouter."""
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.OPENROUTER_API_KEY,
    )

def is_payment_required_error(error):
    """Check if the error is related to payment requirements."""
    error_str = str(error).lower()
    return any(term in error_str for term in ['402', 'insufficient', 'payment', 'balance', 'diem'])

def is_rate_limit_error(error):
    """Check if the error is related to rate limiting."""
    error_str = str(error).lower()
    return any(term in error_str for term in ['429', 'rate limit', 'too many requests'])

async def get_chat_completion_async(messages, model_config, timeout=30, response_format=None):
    """Make an async request to a single model with timeout."""
    try:
        client = get_openrouter_client()
        
        # Use asyncio.wait_for to implement timeout
        try:
            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: client.chat.completions.create(
                        model=model_config['name'],
                        messages=messages,
                        temperature=model_config['config']['temperature'],
                        max_tokens=model_config['config']['max_tokens'],
                        extra_headers=settings.OPENROUTER_HEADERS,
                        extra_body={}
                    )
                ),
                timeout=model_config['config']['timeout']
            )
            return {
                'success': True,
                'model': model_config['name'],
                'content': response.choices[0].message.content
            }
        except asyncio.TimeoutError:
            logger.warning(f"Model {model_config['name']} timed out after {model_config['config']['timeout']}s")
            return {
                'success': False,
                'model': model_config['name'],
                'error': 'Request timed out'
            }
    except Exception as e:
        logger.warning(f"Error with model {model_config['name']}: {str(e)}")
        return {
            'success': False,
            'model': model_config['name'],
            'error': str(e)
        }

async def get_chat_completion(messages, model_name=None, max_attempts=3, response_format=None):
    """
    Get chat completion with fast failover between models.
    
    Args:
        messages (list): List of message dictionaries with 'role' and 'content'
        model_name (str, optional): Specific model to try first. Defaults to None
        max_attempts (int, optional): Maximum number of models to try. Defaults to 3
        
    Returns:
        dict: {
            'success': bool,
            'content': str or None,
            'model': str or None,
            'error': str or None
        }
    """
    # If a specific model is requested, try it first
    models_to_try = []
    if model_name:
        models_to_try = [m for m in MODEL_PRIORITY if m['name'] == model_name]
    
    # Add remaining models up to max_attempts
    remaining_slots = max_attempts - len(models_to_try)
    if remaining_slots > 0:
        for model in MODEL_PRIORITY:
            if model not in models_to_try:
                models_to_try.append(model)
                remaining_slots -= 1
                if remaining_slots <= 0:
                    break
    
    # Create tasks for all models we want to try
    tasks = [get_chat_completion_async(messages, model) for model in models_to_try]
    
    # Wait for the first successful response
    for future in asyncio.as_completed(tasks):
        result = await future
        if result['success']:
            logger.info(f"Successfully got response from {result['model']}")
            return {
                'success': True,
                'content': result['content'],
                'model': result['model'],
                'error': None
            }
    
    # If we get here, all attempts failed
    return {
        'success': False,
        'content': None,
        'model': None,
        'error': 'All model attempts failed. Please try again later.'
    }

def get_chat_completion_sync(messages, model_name=None, max_attempts=3, response_format=None):
    """Synchronous wrapper for the async get_chat_completion function.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        model_name: Optional specific model to try first
        max_attempts: Maximum number of models to try
        response_format: Optional format for the response (e.g., {'type': 'json_object'})
        
    Returns:
        dict: Response with 'success', 'content', 'model', and 'error' keys
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            get_chat_completion(
                messages=messages,
                model_name=model_name,
                max_attempts=max_attempts,
                response_format=response_format
            )
        )
    finally:
        loop.close()
