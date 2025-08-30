#!/usr/bin/env python3
"""
Start script for the Scribble in Time Backend Django application using Gunicorn.
"""
import os
import sys
import subprocess

def main():
    # Set the Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scribbleintimeai.settings')
    
    # Gunicorn command with correct arguments
    cmd = [
        'gunicorn',
        '--bind', '0.0.0.0:8080',
        '--workers', '3',
        '--timeout', '30',
        '--access-logfile', '-',
        '--error-logfile', '-',
        '--log-level', 'info',
        'scribbleintimeai.wsgi:application'
    ]
    
    print("Starting Scribble in Time Backend with Gunicorn...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 