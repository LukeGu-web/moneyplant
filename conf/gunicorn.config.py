command = '/home/lukegu/Github/moneyplant/plant/bin/gunicorn'
pythonpath = '/home/lukegu/Github/moneyplant'
bind = '192.168.31.221:8000'
workers = 3

# Additional configurations for better performance with Celery
worker_class = 'sync'
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = '/home/lukegu/Github/moneyplant/logs/gunicorn-access.log'
errorlog = '/home/lukegu/Github/moneyplant/logs/gunicorn-error.log'
loglevel = 'info'

# Process naming
proc_name = 'moneyplant_gunicorn'

# Recommended for production
preload_app = True


def post_fork(server, worker):
    """
    Called just after a worker has been forked.
    """
    from psycogreen.gevent import patch_psycopg
    patch_psycopg()

    # Reset Celery connection pool after fork
    from celery import current_app
    current_app.connection_pool.force_close_all()


def when_ready(server):
    """
    Called just before the master process is initialized.
    """
    # Ensure Celery Beat isn't started with each worker
    if not server.cfg.worker_id:
        from celery import current_app
        current_app.connection_pool.force_close_all()
