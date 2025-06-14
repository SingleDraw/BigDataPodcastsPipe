import datetime
import pyarrow.parquet as pq
from app.src.apis.i_tunes_api import ITunesAPI
from app.src.apis.podcast_index_api import PodcastIndexAPI
from app.src.api_manager import PodcastApiManager
from app.src.logger import logger
from app.src.enricher import Enricher
from app.src.get_latest_scrape_timestamp import get_latest_scrape_timestamp
from typing import List, Optional, Literal


def run_enricher(
        storage_client_constructor,

        # Sink parameters
        container_name: str,
        sink_dir: str,
        source_dir: str,
        transcription_dir: str,
        overwrite: bool,
        

        azure_storage_account: str,
        azure_storage_key: str = "",

        s3_access_key: str = "",
        s3_secret_key: str = "",
        s3_endpoint_url: str = "",
        s3_use_ssl: Optional[bool] = None,
        s3_region_name: str = "",

        podcasting_index_api_key: str = "",
        podcasting_index_api_secret: str = "",

        # Enrichment parameters
        fallback_range_days: int = 2,  
        top: int = 15,  
        podcast_api_search_limit: int = 3,
        countries: Optional[List[str]] = ["us", "pl"],
        title_clustering_threshold: int = 80,
        filter_genre: str = "*",
        master_limit: int = 50,
        podcast_title_search_threshold: int = 90,
        episodes_limit: int = 5,
        batch_jobs_limit: int = 3,
        round_robin_batch_jobs: bool = True,
        verbose: bool = True,

        # batch job parameters
        target_storage_name: str = 'default',           # Default storage name for the output path [whisperer config]
        target_protocol: Literal["s3", "az"] = "az",    # Default protocol for the output path  [whisperer config]       
        
        # Retry parameters
        delay: int = 1,     # Delay in seconds between retries
        retries: int = 3    # Number of retries for storage upload failures
    ):
    try:
        # Construct the storage credentials
        storage_credentials = {
            "azure_storage_account": azure_storage_account,
            "azure_storage_key": azure_storage_key,
            "s3_access_key": s3_access_key,
            "s3_secret_key": s3_secret_key,
            "s3_endpoint_url": s3_endpoint_url,
            "s3_use_ssl": s3_use_ssl,
            "s3_region_name": s3_region_name
        }

        # Initialize the storage client
        storage_client = storage_client_constructor(
            credentials=storage_credentials
        )

        # Initialize the API manager with the necessary APIs
        api_manager = PodcastApiManager(
            itunes_api=ITunesAPI(),
            podcasting_index_api=PodcastIndexAPI(
                api_key=podcasting_index_api_key,
                api_secret=podcasting_index_api_secret
            )
        )

        # Get the latest scrape timestamp
        logger.info("Fetching the latest scrape timestamp...")
        latest_storage_key = f"{source_dir}/latest.json"
        # since: int = get_latest_scrape_timestamp(
        #     storage_client=storage_client,
        #     container_name=container_name,
        #     storage_key=latest_storage_key,
        #     fallback_range_days=fallback_range_days
        # )
        last_day = int(round(datetime.datetime.now(
            tz=datetime.timezone.utc  # Ensure we use UTC for consistency
        ).timestamp() - 60 * 60 * 24)) # 1 day ago

        since = last_day

        # load the DataFrame from Azure Blob Storage
        date_key = datetime.datetime.now().strftime("%Y-%m-%d")
        podcasts_storage_key = f"{source_dir}/date={date_key}/top_podcasts.parquet"

        logger.info(f"Reading Parquet file from {podcasts_storage_key} in container {container_name}")
        bytesIO = storage_client.download_object(
            container_name=container_name,
            storage_key=podcasts_storage_key
        )
        table = pq.read_table(bytesIO)
        df = table.to_pandas()

        # Initialize and run the Enricher
        _ = (
            Enricher(
                df=df,
                api_manager=api_manager,
                enrichment_params={
                    'top': top,
                    'countries': countries,
                    'title_clustering_threshold': title_clustering_threshold,
                    'filter_genre': filter_genre,
                    'master_limit': master_limit,
                    'podcasts_api_search_limit': podcast_api_search_limit,
                    'podcast_title_search_threshold': podcast_title_search_threshold,
                    'episodes_fetch_limit_per_podcast': episodes_limit,
                    'since_date_fetch': since
                }
            )
            .run_pipelines()
            .generate_batch_job_json(
                jobs_limit=batch_jobs_limit,
                round_robin=round_robin_batch_jobs,
                target_storage_name=target_storage_name,
                target_protocol=target_protocol,
                container_name=container_name,
                transcription_dir=transcription_dir,
            )
            .save_results(
                storage_client=storage_client,
                verbose=verbose,
                sink_dir=sink_dir,
                overwrite=overwrite,
                container_name=container_name,
                date_key=date_key
                # TODO: retries and delay should be handled in the storage client or a retry decorator
            )
        )
        logger.info("Enrichment process completed successfully.")

    except Exception as e:
        print(f"An error occurred during the enrichment process: {e}")
        logger.error(f"An error occurred during the enrichment process: {e}")
        raise




