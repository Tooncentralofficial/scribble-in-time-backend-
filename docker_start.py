#!/usr/bin/env python3
"""
Docker-specific startup script for Railway deployment
"""
import os
import sys
import subprocess
import time

def main():
    # Set Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scribbleintimeai.settings')
    
    # Get port from Railway environment
    port = os.environ.get('PORT', '8080')
    
    print("Starting Docker deployment...")
    
    # Create static directory if it doesn't exist
    from pathlib import Path
    static_dir = Path(__file__).resolve().parent / "static"
    if not static_dir.exists():
        print("Creating static directory...")
        static_dir.mkdir(exist_ok=True)
        # Create a placeholder file
        placeholder_file = static_dir / "placeholder.css"
        placeholder_file.write_text("/* Static files placeholder */")
        print("✓ Static directory created")
    
    # Wait for database to be ready (for Railway)
    print("Waiting for database to be ready...")
    time.sleep(5)  # Give database time to initialize
    
    # Run migrations with retry logic
    print("Running database migrations...")
    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = subprocess.run(
                [sys.executable, 'manage.py', 'migrate'], 
                capture_output=True, 
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                print("✓ Migrations completed successfully")
                break
            else:
                print(f"⚠ Migration attempt {attempt + 1} failed: {result.stderr}")
                if attempt < max_retries - 1:
                    print("Retrying in 10 seconds...")
                    time.sleep(10)
                else:
                    print("⚠ Migrations failed, continuing anyway...")
        except subprocess.TimeoutExpired:
            print(f"⚠ Migration attempt {attempt + 1} timed out")
            if attempt < max_retries - 1:
                print("Retrying in 10 seconds...")
                time.sleep(10)
            else:
                print("⚠ Migrations timed out, continuing anyway...")
        except Exception as e:
            print(f"⚠ Migration error: {e}")
            if attempt < max_retries - 1:
                print("Retrying in 10 seconds...")
                time.sleep(10)
            else:
                print("⚠ Migrations failed, continuing anyway...")
    
    # Collect static files
    print("Collecting static files...")
    try:
        result = subprocess.run(
            [sys.executable, 'manage.py', 'collectstatic', '--noinput'], 
            capture_output=True, 
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print("✓ Static files collected successfully")
        else:
            print(f"⚠ Static files warning: {result.stderr}")
    except Exception as e:
        print(f"⚠ Static files error: {e}")
    
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
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 