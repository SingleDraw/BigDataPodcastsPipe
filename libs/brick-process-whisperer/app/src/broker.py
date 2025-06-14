import os
import redis

""" 
Redis client for the broker.
This is used to submit, retrieve and track the progress of transcription jobs.
"""
broker = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis-whisperer"), 
    port=os.getenv("REDIS_PORT", 6379), 
    db=os.getenv("REDIS_DB", 0),
    decode_responses=True
)

# password=os.getenv("REDIS_PASSWORD", None),