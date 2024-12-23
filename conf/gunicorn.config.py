# Path to the Gunicorn executable
command = '/home/lukegu/Github/moneyplant/venv/bin/gunicorn'

# Path to the Django project
pythonpath = '/home/lukegu/Github/moneyplant'

# Server binding address and port
bind = '192.168.31.221:8000'

# Number of worker processes
workers = 3

# Worker settings
worker_class = 'sync'  # Sync workers; change if using asynchronous workers
timeout = 120          # Worker timeout in seconds
keepalive = 5          # Keep connections alive
max_requests = 1000    # Restart worker after handling this many requests
max_requests_jitter = 50  # Add random jitter to avoid simultaneous restarts

# Logging
accesslog = '/home/lukegu/Github/moneyplant/logs/gunicorn-access.log'
errorlog = '/home/lukegu/Github/moneyplant/logs/gunicorn-error.log'
loglevel = 'info'

# Process naming
proc_name = 'moneyplant_gunicorn'

# Preload the app for better performance in production
preload_app = True


# Hook for actions after a worker is forked
def post_fork(server, worker):
    """
    Called just after a worker has been forked.
    Useful for patching libraries or initializing workers.
    """
    try:
        from psycogreen.gevent import patch_psycopg
        patch_psycopg()

        # Reset Celery connection pool after fork
        from celery import current_app
        current_app.connection_pool.force_close_all()
    except ImportError:
        server.log.warning("psycogreen or Celery not installed. Skipping patches.")


# Hook for actions when Gunicorn is ready
def when_ready(server):
    """
    Called just before the master process is initialized.
    Useful for ensuring necessary services or tasks are prepared.
    """
    server.log.info("Gunicorn server is ready.")
