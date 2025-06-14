from datetime import datetime

"""
Configuration for the Enrichment Pipeline
This module defines constants and paths used in the enrichment pipeline.
"""

CONTAINER_NAME = "whisperer"
SOURCE_DIR = "raw_podcasts_data"
SINK_DIR = "full_podcasts_data"
TRANSCRIPTION_DIR = "transcriptions"
DIR_DATE = datetime.now().strftime("%Y-%m-%d")

# syntax: whisperer/raw_podcasts_data/date=2025-06-11/top_podcasts.parquet
# This file stores the raw data scraped by the scraper
PODCASTS_STORAGE_KEY = f"{SOURCE_DIR}/date={DIR_DATE}/top_podcasts.parquet"
RESULTS_STORAGE_KEY = f"{SOURCE_DIR}/date={DIR_DATE}/scrape_job_status.parquet"

# syntax: whisperer/full_podcasts_data/date=2025-06-11/top_podcasts.parquet
# This file stores the enriched data
TARGET_JOBS_STORAGE_KEY = f"{SINK_DIR}/date={DIR_DATE}"

# syntax: whisperer/raw_podcasts_data/latest.json
# This file stores the latest timestamp of the scrape job
LATEST_STORAGE_KEY = f"{SOURCE_DIR}/latest.json"

# syntax: whisperer/full_podcasts_data/latest.json
TARGET_LATEST_STORAGE_KEY = f"{SINK_DIR}/latest.json"
