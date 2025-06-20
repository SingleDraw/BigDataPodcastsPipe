from kombu import Queue
from app.settings import (
    broker_url, result_backend, chunk_cleanup_timeout,
    task_soft_time_limit, task_time_limit, visibility_timeout
)

# Broker settings
broker_url = broker_url
result_backend = result_backend

# Task routing
task_routes = {
    'app.src.transcribe.transcribe': {'queue': 'transcription_queue'},
}

# Queue definitions
task_queues = (
    Queue('transcription_queue', routing_key='whisper_transcription'),
    Queue('default', routing_key='default'),
)

# Default queue
task_default_queue = 'transcription_queue'
task_default_exchange_type = 'direct'
task_default_routing_key = 'whisper_transcription'

# Worker settings
worker_prefetch_multiplier = 1
task_acks_late = True
worker_send_task_events = True

# Serialization
task_serializer = 'json'
accept_content = ['json']
result_serializer = 'json'
timezone = 'Europe/Warsaw'

# -------------------------------------------------------------------------------------
# Task timing settings
task_soft_time_limit=task_soft_time_limit  # soft timeout: raises SoftTimeLimitExceeded
task_time_limit=task_time_limit     # hard timeout: forcibly kills task

# Broker settings for proper task requeuing
broker_transport_options={
    # Redis specific settings for KEDA compatibility
    'priority_steps': list(range(10)),
    'queue_order_strategy': 'priority',
    'sep': ':',
    # Celery specific settings
    "visibility_timeout": visibility_timeout, # visibility_timeout,  # time to process task, before it becomes visible again for requeue
    "max_retries": 3,               # Retry up to 3 times if task fails
    "retry_policy": {
        "timeout": 30              # Retry after 30 seconds
    }
}  

# Worker settings
# worker_prefetch_multiplier=1       # Prefetch only one task at a time
# worker_disable_rate_limits=True    # Disable rate limits

# Task settings and recovery
task_track_started =True           # Track task start time
task_acks_late=True                # This should be at app level too
task_reject_on_worker_lost=True    # Ensure tasks are requeued if worker dies

# Result backend settings
result_expires=3600                # Results expire after 1 hour
result_persistent=True

worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'


# Task tracking settings
task_acks_on_failure_or_timeout = True   # ack on failure or timeout