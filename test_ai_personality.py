#!/usr/bin/env python3
"""
Test script to demonstrate the new AI personality and response style
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scribbleintimeai.settings')
django.setup()

from chat.ai_service import AIService

def test_ai_responses():
    """Test various types of questions to demonstrate the new AI personality"""
    
    # Test session ID for memory management
    session_id = "test_session_123"
    
    test_questions = [
        "What services do you offer?",
        "Can you tell me more about your pricing?",
        "I'd like a detailed explanation of your process",
        "What makes your business different?",
        "Can you be more expansive about your experience?",
        "Tell me about your background",
        "What should I expect when working with you?",
        "I want comprehensive details about your approach",
        "What did we discuss earlier about your services?",  # Test memory
        "I don't have information about something not in your documents"  # Test confidence referral
    ]
    
    print("Testing AI Personality and Response Style")
    print("=" * 50)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{i}. Question: {question}")
        print("-" * 30)
        
        try:
            response = AIService.get_ai_response(question, session_id=session_id)
            print(f"Response: {response['message']}")
            
            # Check confidence level
            if 'confidence' in response:
                print(f"Confidence: {response['confidence']}")
            
            # Check if referral was added
            if 'contact.ascribbleintime@gmail.com' in response['message']:
                print("✓ Referral to human contact included")
            
            # Check if response is personalized
            if any(word in response['message'].lower() for word in ['i ', 'my ', 'we ', 'our ']):
                print("✓ Response uses first person (personalized)")
            else:
                print("✗ Response may not be personalized enough")
                
            # Check response length
            if len(response['message']) > 200:
                print("✓ Detailed response provided")
            else:
                print("ℹ Brief response (may offer to elaborate)")
                
        except Exception as e:
            print(f"Error: {str(e)}")
        
        print()

if __name__ == '__main__':
    test_ai_responses() 