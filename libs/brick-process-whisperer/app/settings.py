import os

"""
Read environment variables and set default values for the application settings.
Single source of truth for env based configuration.
"""

# Setup Redis broker URL
host=os.getenv("REDIS_HOST", "redis-whisperer")
port=os.getenv("REDIS_PORT", 6379)
db=os.getenv("REDIS_DB", 0)

broker_url = os.environ.get('CELERY_BROKER_URL', f"redis://{host}:{port}/{db}")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "rpc://")

# Calculate visibility timeout based on task duration + buffer
task_soft_time_limit = max( 0, float(os.getenv("TASK_SOFT_TIME_LIMIT", 600)) )
# task_time_limit = max(task_soft_time_limit + 50, int(os.getenv("TASK_TIME_LIMIT", 650)))
task_time_limit = max(task_soft_time_limit + 5, int(os.getenv("TASK_TIME_LIMIT", 650)))
visibility_timeout = task_time_limit + 60       # Add 60 second buffer

# Chunk cleanup timeout
chunk_cleanup_timeout = int(os.getenv("CHUNK_CLEANUP_TIMEOUT", 3600))

# Max duration for a chunk
max_duration = float(os.getenv("CHUNK_MAX_DURATION", 600))
default_retry_delay = float(os.getenv("DEFAULT_RETRY_DELAY", 30))      # retry delay in seconds
max_retries = int(os.getenv("MAX_RETRIES", 3))                         # max retries

# Retry configuration for tasks
retry_kwargs={
    "max_retries": max_retries,         # max retries
    "countdown": default_retry_delay    # delay between retries
}

cleanup_timeout = max(
    float(os.getenv("CHUNK_CLEANUP_TIMEOUT", 600)), 
    float(os.getenv("TASK_SOFT_TIME_LIMIT", 600)) + 60
) 
