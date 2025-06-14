#!/bin/bash

set -a
# shellcheck disable=SC1091
source .env
set +a

echo "PODCAST_INDEX_API_KEY=${PODCASTING_INDEX_API_KEY:-your_api_key}"
echo "PODCAST_INDEX_API_SECRET=${PODCASTING_INDEX_API_SECRET:-your_api_secret}"