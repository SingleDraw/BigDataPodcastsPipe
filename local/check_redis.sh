#!/bin/bash

# # Check if redis-cli is installed
# if ! command -v redis-cli &> /dev/null; then
#     echo "redis-cli could not be found. Proceeding to install it..."
#     # Install redis-cli if not found
#     if [[ "$OSTYPE" == "linux-gnu"* ]]; then
#         sudo apt-get update
#         sudo apt-get install -y redis-tools
#     elif [[ "$OSTYPE" == "darwin"* ]]; then
#         brew install redis
#     else
#         echo "Unsupported OS. Please install redis-cli manually."
#         exit 1  
#     fi
# fi

# Run docker ith redis-cli to connect to the Redis container
# Ensure you have Docker installed and running
# docker run -it --rm \
#     --network host \
#     redis:latest redis-cli -h whisperer-redis -p 6379 -n 0

# check redis list queue length inside the container
# echo "Checking Redis list queue length..."
# docker run -it --rm \
#     --network host \
#     redis:latest redis-cli -h redis-whisperer -p 6379 -n 0 LLEN transcription_queue
docker run -it --rm \
    --network host \
    redis:latest redis-cli -h localhost -p 6379 -n 0 LLEN transcription_queue

# # Debug script to check what keys Celery creates in Redis
# # Run this by exec'ing into your Redis container

# echo "=== Redis Keys Analysis ==="
# echo "Connecting to Redis..."

# # Check all keys in database 0
# echo -e "\n1. All keys in database 0:"
# redis-cli -h whisperer-redis -p 6379 -n 0 KEYS "*"

# # Check specifically for celery-related keys
# echo -e "\n2. Celery-related keys:"
# redis-cli -h whisperer-redis -p 6379 -n 0 KEYS "*celery*"

# # Check the type of the 'celery' key if it exists
# echo -e "\n3. Type of 'celery' key:"
# redis-cli -h whisperer-redis -p 6379 -n 0 TYPE celery

# # Check length of celery queue if it's a list
# echo -e "\n4. Length of 'celery' list (if it exists):"
# redis-cli -h whisperer-redis -p 6379 -n 0 LLEN celery

# # Check for other common Celery Redis patterns
# echo -e "\n5. Other possible Celery keys:"
# redis-cli -h whisperer-redis -p 6379 -n 0 KEYS "*queue*"
# redis-cli -h whisperer-redis -p 6379 -n 0 KEYS "*task*"

# echo -e "\n=== End Analysis ==="