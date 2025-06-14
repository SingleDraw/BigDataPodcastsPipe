import typer, os
from app.app import run_enricher
from typing import List, Optional

if os.getenv("ENVIRONMENT") != "production":
    #from app.src.storage.local_client import LocalStorageClient as StorageClient
    from storage_lib import LocalStorageClient as StorageClient
    from pathlib import Path
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
else:
    # from app.src.storage.client import StorageClient
    from storage_lib import StorageClient

def parse_comma_env(value: Optional[str]) -> Optional[List[str]]:
    return value.split(",") if value else None

countries_env = parse_comma_env(os.getenv("COUNTRIES", "us,pl"))

app = typer.Typer()


@app.command("enrich")
def enrich_cmd(
    # Azure Blob Storage parameters
    azure_storage_account: Optional[str] = typer.Option(
        os.getenv("AZURE_STORAGE_ACCOUNT", ""), 
        help="Azure Storage Account name"
    ),
    # S3 parameters
    s3_access_key: Optional[str] = typer.Option(
        os.getenv("S3_ACCESS_KEY", ""),
        help="S3 Access Key"
    ),
    # Sink parameters
    overwrite: bool = typer.Option(
        False, 
        help="Overwrite blobs if they already exist"
    ),
    container_name: Optional[str] = typer.Option(
        os.getenv("SINK_CONTAINER_NAME", "whisperer"), 
        help="Container name for the sink"
    ),


    sink_dir: Optional[str] = typer.Option(
        os.getenv("SINK_DIR", "full_podcasts_data"), 
        help="Directory name for the sink"
    ),
    source_dir: Optional[str] = typer.Option(
        os.getenv("SOURCE_DIR", "raw_podcasts_data"), 
        help="Directory name for the source"
    ),
    transcription_dir: Optional[str] = typer.Option(
        os.getenv("TRANSCRIPTION_DIR", "transcriptions"), 
        help="Directory name for the transcriptions"
    ),

    target_storage_name: str = typer.Option(
        os.getenv("TARGET_STORAGE_NAME", "default"),
        "--target-storage-name", "-tsn",
        help="Default storage name for the output path [whisperer config]"
    ),
    target_protocol: Optional[str] = typer.Option(
        os.getenv("TARGET_PROTOCOL", "az"),
        "--target-protocol", "-tp",
        help="Default protocol for the output path [whisperer config]. Options: 's3', 'az'"
    ),


    # parameters from environment variables
    fallback_range_days: int = typer.Option(
        int(os.getenv("FALLBACK_RANGE_DAYS", 2)), 
        "--fallback-range-days", "-frd",
        help="Days to look back if latest scrap date isn't available from stamp"
    ),
    top: int = typer.Option(
        int(os.getenv("TOP", 15)), 
        "--top", "-t",
        help="Default to top number podcasts in master ranking"
    ),
    podcast_api_search_limit: int = typer.Option(
        int(os.getenv("PODCAST_API_SEARCH_LIMIT", 3)), 
        "--podcast-api-search-limit", "-pasl",
        help="Limit for the number of podcasts to search for missing IDs"
    ),
    countries: List[str] = typer.Option(
        countries_env,
        "--countries", "-co",
        help="Comma-separated list of countries to scrape podcasts from",
        show_default=False
    ),
    title_clustering_threshold: int = typer.Option(
        int(os.getenv("TITLE_CLUSTERING_THRESHOLD", 80)), 
        "--title-clustering-threshold",
        "--clustering-threshold", "-ct",
        help="Threshold for podcast title clustering (0-100) - default 80"
    ),
    filter_genre: str = typer.Option(
        os.getenv("FILTER_GENRE", "*"), 
        "--filter-genre", "-fg",
        "--genre", "-g",
        help="Filter podcasts by genre (e.g., 'top_podcasts', 'news', 'trending'), default is '*' for all genres"
    ),
    master_limit: int = typer.Option(
        int(os.getenv("MASTER_LIMIT", 50)), 
        "--master-limit", "-ml",
        help="Limit for the number of podcasts in the master ranking"
    ),
    podcast_title_search_threshold: int = typer.Option(
        int(os.getenv("PODCAST_TITLE_SEARCH_THRESHOLD", 90)), 
        "--podcast-title-search-threshold", "-pts",
        help="Threshold for fuzzy matching of podcast titles for API search results (0-100) - default 90"
    ),
    episodes_limit: int = typer.Option(
        int(os.getenv("EPISODES_LIMIT", 5)), 
        help="Limit the number of episodes to fetch for each podcast (default is 5)"
    ),
    batch_jobs_limit: int = typer.Option(
        int(os.getenv("BATCH_JOBS_LIMIT", 3)), 
        "--batch-jobs-limit", "-bjl",
        help="Limit the number of batch jobs to generate per country ranking (default is 3)"
    ),
    round_robin_batch_jobs: bool = typer.Option(
        os.getenv("ROUND_ROBIN_BATCH_JOBS", "true").lower() in ["true", "1", "yes", "y", "on", "enable", "enabled"],
        "--round-robin", "-rr",
        "--round-robin-batch-jobs",
        help="Use round-robin distribution for batch jobs (default is True)"
    ),
    verbose: bool = typer.Option(
        os.getenv("VERBOSE", "false").lower() in ["true", "1", "yes", "y", "on", "enable", "enabled"],
        "--verbose", "-v",
        help="Enable verbose output for debugging (default is False)"
    ),



    # Retry parameters
    delay: int = typer.Option(
        1, 
        help="Delay in seconds between retries for storage upload failures"
    ),
    retries: int = typer.Option(
        3, 
        help="Number of retries for storage upload failures"
    )
    
):
    try:
        run_enricher(        
            storage_client_constructor=StorageClient,

            # Sink parameters
            container_name=container_name, 
            sink_dir=sink_dir,
            source_dir=source_dir,
            transcription_dir=transcription_dir,
            overwrite=overwrite,

            # Output Batch Job parameters
            target_storage_name=target_storage_name,
            target_protocol=target_protocol,

            # Azure Blob Storage credentials
            azure_storage_account=azure_storage_account,
            # -- sensitive data passed as environment variables
            azure_storage_key=os.getenv("AZURE_STORAGE_KEY", ""),

            # S3 credentials
            s3_access_key = s3_access_key,
            # -- sensitive data passed as environment variables
            s3_secret_key = os.getenv("S3_SECRET_KEY", ""),
            s3_endpoint_url = os.getenv("S3_ENDPOINT_URL", ""),
            s3_use_ssl = os.getenv("S3_USE_SSL", None),
            s3_region_name = os.getenv("S3_REGION_NAME", ""),

            # podcasting index API key
            podcasting_index_api_key=os.getenv("PODCAST_INDEX_API_KEY", ""),
            podcasting_index_api_secret=os.getenv("PODCAST_INDEX_API_SECRET", ""),

            # Enrichment parameters
            fallback_range_days=fallback_range_days,
            top=top,
            podcast_api_search_limit=podcast_api_search_limit,
            countries=countries,
            title_clustering_threshold=title_clustering_threshold,
            filter_genre=filter_genre,
            master_limit=master_limit,
            podcast_title_search_threshold=podcast_title_search_threshold,
            episodes_limit=episodes_limit,
            batch_jobs_limit=batch_jobs_limit,
            round_robin_batch_jobs=round_robin_batch_jobs,
            verbose=verbose,

            # Sink parameters
            delay=delay,
            retries=retries
        )


    except Exception as e:
        typer.echo(f"An error occurred during enrichment: {e}")
        typer.echo("Please check your configuration and try again.")
        raise typer.Exit(code=1)
    
    # except Exception as e:
    #     import traceback
    #     typer.echo(f"An error occurred during enrichment: {e}")
    #     traceback.print_exc()  # Logs full traceback to stderr
    #     typer.echo("Please check your configuration and try again.")
    #     raise typer.Exit(code=1)


if __name__ == "__main__":
    app()







# # ----------------

# from azure.identity import DefaultAzureCredential
# from azure.keyvault.secrets import SecretClient

# key_vault_url = "https://<your-keyvault-name>.vault.azure.net/"
# credential = DefaultAzureCredential()  # Automatically uses Azure CLI creds locally
# client = SecretClient(vault_url=key_vault_url, credential=credential)

# secret = client.get_secret("PodcastingIndexApiKey").value
# print(secret)
