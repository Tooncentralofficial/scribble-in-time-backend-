#!/usr/bin/env python3
"""
Startup script for Railway deployment
"""
import os
import subprocess
import sys

def main():
    # Set Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scribbleintimeai.settings')
    
    # Get port from Railway environment
    port = os.environ.get('PORT', '8080')
    
    # Run migrations
    print("Running database migrations...")
    subprocess.run([sys.executable, 'manage.py', 'migrate'], check=True)
    
    # Collect static files
    print("Collecting static files...")
    subprocess.run([sys.executable, 'manage.py', 'collectstatic', '--noinput'], check=True)
    
    # Start gunicorn
    print(f"Starting server on port {port}...")
    cmd = [
        'gunicorn',
        '--bind', f'0.0.0.0:{port}',
        '--workers', '3',
        '--timeout', '30',
        '--access-logfile', '-',
        '--error-logfile', '-',
        '--log-level', 'info',
        'scribbleintimeai.wsgi:application'
    ]
    
    subprocess.run(cmd, check=True)

if __name__ == '__main__':
    main() 