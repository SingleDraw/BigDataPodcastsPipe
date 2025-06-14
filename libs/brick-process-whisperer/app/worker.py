import os
import logging
import threading, time
from pathlib import Path
from celery import Celery
from celery.signals import after_setup_logger, worker_ready

APP_ROOT_DIR_NAME = 'app'

# Setup Redis broker URL
host=os.getenv("REDIS_HOST", "redis-whisperer")
port=os.getenv("REDIS_PORT", 6379)
db=os.getenv("REDIS_DB", 0)
broker = f"redis://{host}:{port}/{db}"

# visibility_timeout = int(os.getenv("BROKER_VISIBILITY_TIMEOUT", 3600))
# Calculate visibility timeout based on task duration + buffer
task_time_limit = int(os.getenv("TASK_TIME_LIMIT", 650))
task_time_limit = task_time_limit if task_time_limit > 60 else 650
task_soft_time_limit = task_time_limit - 50  # soft timeout: raises SoftTimeLimitExceeded
visibility_timeout = task_time_limit + 60  # Add 60 second buffer

# Periodic cleanup of temporary files
# This function will run in a separate thread to clean up temporary files
# as fallback for the main task cleanup
def cleanup_tmp():
    while True:
        now = time.time()
        for f in Path("/tmp").iterdir():
            try:
                if f.is_file() and (now - f.stat().st_mtime) > int(os.getenv("CHUNK_CLEANUP_TIMEOUT", 3600)):
                    f.unlink()
            except:
                pass
        time.sleep(60)



app = Celery(
    "whisper_worker",
    broker=broker,  
    backend="rpc://"
)

app.conf.update(

    # Task timing settings
    task_soft_time_limit=task_soft_time_limit,  # soft timeout: raises SoftTimeLimitExceeded
    task_time_limit=task_time_limit,       # hard timeout: forcibly kills task

    # Broker settings for proper task requeuing
    broker_transport_options={
        "visibility_timeout": visibility_timeout, # visibility_timeout,  # time to process task, before it becomes visible again for requeue
        "max_retries": 3,               # Retry up to 3 times if task fails
        "retry_policy": {
            "timeout": 30,              # Retry after 30 seconds
        }

    },  

    # Worker settings
    worker_prefetch_multiplier=1,    # Prefetch only one task at a time
    worker_disable_rate_limits=True, # Disable rate limits

    # Task settings and recovery
    task_track_started =True,           # Track task start time
    task_acks_late=True,                # This should be at app level too
    task_reject_on_worker_lost=True,    # Ensure tasks are requeued if worker dies

    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_persistent=True,

    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    
)

app.conf.include = [
    f"{APP_ROOT_DIR_NAME}.src.transcribe",
]

@worker_ready.connect
def at_worker_start(**kwargs):
    threading.Thread(target=cleanup_tmp, daemon=True).start()

# Setup logging (will print to stdout)
@after_setup_logger.connect
def setup_loggers(logger, *args, **kwargs):
    logger.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)