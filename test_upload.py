#!/usr/bin/env python3
"""
Test script for document upload endpoint
"""
import requests
import os
import sys

def test_upload_endpoint(file_path):
    """Test the document upload endpoint"""
    
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist")
        return False
    
    # Check file type
    file_ext = file_path.split('.')[-1].lower()
    if file_ext not in ['pdf', 'txt', 'md', 'docx']:
        print(f"Error: Unsupported file type: {file_ext}")
        return False
    
    url = 'http://localhost:8000/api/chat/documents/upload/'
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'application/octet-stream')}
            
            print(f"Uploading {file_path} to {url}")
            print(f"File size: {os.path.getsize(file_path)} bytes")
            
            response = requests.post(url, files=files)
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 201:
                result = response.json()
                print("✅ Upload successful!")
                print(f"Document ID: {result.get('id')}")
                print(f"Title: {result.get('title')}")
                print(f"Status: {result.get('status')}")
                return True
            else:
                print("❌ Upload failed!")
                try:
                    error_data = response.json()
                    print(f"Error: {error_data.get('error', 'Unknown error')}")
                except:
                    print(f"Error: {response.text}")
                return False
                
    except requests.exceptions.ConnectionError:
        print("❌ Connection error: Make sure the Django server is running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python test_upload.py <file_path>")
        print("Example: python test_upload.py test.pdf")
        sys.exit(1)
    
    file_path = sys.argv[1]
    success = test_upload_endpoint(file_path)
    
    if success:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n💥 Test failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 