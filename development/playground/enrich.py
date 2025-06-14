import os, dotenv, datetime
from src.apis.i_tunes_api import ITunesAPI
from src.apis.podcast_index_api import PodcastIndexAPI
import pandas as pd
import pyarrow.parquet as pq
from storage_lib import StorageClient
from src.api_manager import PodcastApiManager
from src.logger import logger
from src.enricher import Enricher
dotenv.load_dotenv()

from typing import Optional
from src.config import (
    CONTAINER_NAME,
    PODCASTS_STORAGE_KEY,
    LATEST_STORAGE_KEY
)

"""
    Podcast Metadata Provider App
    pip install azure-storage-blob azure-identity uvicorn fastapi requests pandas pyarrow python-dotenv playwright rapidfuzz
"""
credentials={
    # -- Local S3 Storage --
    "s3_access_key": "your_access_key",
    "s3_secret_key": "your_secret_key",
    # "s3_endpoint_url": "http://host.docker.internal:8333", <-- for Dockerized applications
    "s3_endpoint_url": "http://localhost:8333", 
    "s3_use_ssl": False
}

storage_client = StorageClient(
    credentials=credentials
)

# Initialize PodcastApiManager with APIs
api_manager = PodcastApiManager(
    itunes_api=ITunesAPI(), 
    podcasting_index_api=PodcastIndexAPI(
        api_key=os.getenv('PODCAST_INDEX_API_KEY', ''), 
        api_secret=os.getenv('PODCAST_INDEX_API_SECRET', '')
    )
)





if __name__ == "__main__":

    FALLBACK_RANGE_DAYS = int(os.getenv('FALLBACK_RANGE_DAYS', 2))              # Days to look back if latest date isn't available or is too old

    # 1 read latest.json file from Azure Blob Storage to get the last scraped date
    try:
        # latest_json = data_provider.get_json_from_storage(
        latest_json = storage_client.download_json(
            storage_key=LATEST_STORAGE_KEY,
            container_name=CONTAINER_NAME
        )
    except Exception as e:
        logger.error(f"Error fetching latest.json from Azure Blob Storage: {e}")
        latest_json = None


    # Fallback date to look back if latest date is not available or is too old
    # Default to today minus FALLBACK_RANGE_DAYS
    # latest_scrape_date = datetime.datetime.fromtimestamp(
    #     datetime.datetime.now(
    #         tz=datetime.timezone.utc  # Ensure we use UTC for consistency
    #     ).timestamp() - (FALLBACK_RANGE_DAYS * 24 * 60 * 60)
    # ).strftime('%Y-%m-%d %H:%M:%S')


    # ISO format for latest scrape date
    latest_scrape_date = datetime.datetime.fromtimestamp(
        datetime.datetime.now(
            tz=datetime.timezone.utc  # Ensure we use UTC for consistency
        ).timestamp() - (FALLBACK_RANGE_DAYS * 24 * 60 * 60)
    ).isoformat()  # Default to today minus FALLBACK_RANGE_DAYS

    print(f"latest_scrape_date FALLBACK: {latest_scrape_date}")

    if latest_json:
        # Parse the date from the latest.json file
        try:
            latest_scrape_date = latest_json.get('ISO_date', None)
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing latest.json data: {e}, falling back to FALLBACK_RANGE_DAYS")
    else:
        logger.warning("No latest.json file found in Azure Blob Storage. Using default values.")
    
    logger.info(f"Latest scrape date FINAL: {latest_scrape_date}")
    # print(f"Latest scrape date update: {latest_scrape_date}")

    last_scrape_timestamp = datetime.datetime.fromisoformat(
        latest_scrape_date
    ).timestamp()  # Convert to timestamp
    print(f"last_scrape_timestamp: {last_scrape_timestamp}")

    # # debugging output converting timestamp to datetime
    # last_scrape_datetime = datetime.datetime.fromtimestamp(
    #     last_scrape_timestamp,
    #     tz=datetime.timezone.utc  # Ensure we use UTC for consistency
    # )
    # print(f"last_scrape_datetime: {last_scrape_datetime}")


    last_day = int(round(datetime.datetime.now(
        tz=datetime.timezone.utc  # Ensure we use UTC for consistency
    ).timestamp() - 60 * 60 * 24)) # 1 day ago

    since = last_day

    print(f"since: {since}")

    # exit(0)

    # Master ranking parameters
    TOP=15                              # Default to top number podcasts in master ranking
    PODCAST_API_SEARCH_LIMIT = int(os.getenv('PODCAST_API_SEARCH_LIMIT', 3))  # Limit for the number of podcasts to search for missing IDs
    COUNTRIES = 'us,pl'                 # Default to US and PL podcasts, can be adjusted as needed
    TITLE_CLUSTERING_THRESHOLD = 80     # threshold for fuzzy matching of podcast titles (for creating master ranking)
    FILTER_GENRE = '*'                  # Default to None, can be set to a specific genre like 'top_podcasts', 'News', 'trending'
    MASTER_LIMIT = 50                   # Limit for master ranking of podcasts, can be adjusted as needed

    # Parameters for fetching episodes
    PODCAST_TITLE_SEARCH_THRESHOLD = 90 # threshold for fuzzy matching of podcast titles when searching for podcasts in APIs
    EPISODES_LIMIT = 5                  # Limit for the number of episodes urls to fetch per podcast, can be adjusted as needed  
    
    # Batch job generation parameters    
    BATCH_JOBS_LIMIT = 3                # Limit the number of jobs to generate, can be adjusted as needed
    ROUND_ROBIN_BATCH_JOBS = True       # Use round-robin distribution for jobs, can be set to False to disable round-robin distribution
    
    # Verbose output for debugging
    VERBOSE = True                      # Verbose output for debugging, can be set to False to disable verbose output



    # ---------------------------------------------------------------------------
    # Load the DataFrame from Azure Blob Storage
    bytesIO = storage_client.download_object(
        container_name=CONTAINER_NAME,
        storage_key=PODCASTS_STORAGE_KEY # RESULTS_STORAGE_KEY
    )
    logger.info(
        f"Reading Parquet file from {PODCASTS_STORAGE_KEY} "
        f"in container {CONTAINER_NAME}"
    )
    table = pq.read_table(bytesIO)
    df = table.to_pandas()
    
 

    enricher = (
        Enricher(
            df=df,
            api_manager=api_manager,
            enrichment_params={
                'top': TOP,  # Default to top 10 podcasts, can be adjusted
                'countries': COUNTRIES.split(','),  # Default to US and PL podcasts, can be adjusted as needed
                'title_clustering_threshold': TITLE_CLUSTERING_THRESHOLD,  # Similarity threshold for fuzzy matching
                'filter_genre': FILTER_GENRE,  # Filter for 'top_podcasts' by default, or use '*' as wildcard for all genres
                'master_limit': MASTER_LIMIT,  # Limit the DataFrame to the top N podcasts
                'podcasts_api_search_limit': PODCAST_API_SEARCH_LIMIT,  # Limit for the number of podcasts to search for missing IDs
                'podcast_title_search_threshold': PODCAST_TITLE_SEARCH_THRESHOLD,  # Threshold for fuzzy matching of podcast titles when searching for podcasts in APIs
                'episodes_fetch_limit_per_podcast': EPISODES_LIMIT,  # Limit for the number of episodes urls to fetch per podcast
                'since_date_fetch': since  # Fetch episodes from the date specified, default to last day
            }
        )
        .run_pipelines()
        .generate_batch_job_json(
            jobs_limit=BATCH_JOBS_LIMIT,        # Limit the number of jobs to generate
            round_robin=ROUND_ROBIN_BATCH_JOBS, # Use round-robin distribution for jobs
        )
        .save_results(
            storage_client=storage_client,
            verbose=VERBOSE,                    # Verbose output for debugging
        )
    )