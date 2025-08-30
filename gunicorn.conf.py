# Gunicorn configuration file for Railway deployment
import multiprocessing
import os

# Server socket - use Railway's PORT environment variable
port = os.environ.get('PORT', '8080')
bind = f"0.0.0.0:{port}"
backlog = 2048

# Worker processes - use fewer workers for Railway
workers = min(multiprocessing.cpu_count() * 2 + 1, 4)  # Max 4 workers for Railway
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "scribble-in-time-backend"

# Server mechanics
daemon = False
pidfile = "/tmp/gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# Preload app for better performance
preload_app = True

def when_ready(server):
    server.log.info(f"Server is ready. Spawning workers on port {port}")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_worker_init(worker):
    worker.log.info("Worker initialized (pid: %s)", worker.pid)

def worker_abort(worker):
    worker.log.info("Worker aborted (pid: %s)", worker.pid) 