import typer, os
from app.app import run_pcaster
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

sources_env = parse_comma_env(os.getenv("PCASTER_SOURCES", None))
platforms_env = parse_comma_env(os.getenv("PCASTER_PLATFORMS", None))
countries_env = parse_comma_env(os.getenv("PCASTER_COUNTRIES", None))

app = typer.Typer()


@app.command("scrape")
def scrape_cmd(
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
        os.getenv("SINK_DIR", "raw_podcasts_data"), 
        help="Directory name for the sink"
    ),

    # Scraping parameters
    sources: Optional[List[str]] = typer.Option(
        sources_env,
        "--source", "-s", 
        help="List of sources", 
        show_default=False
    ),
    platforms: Optional[List[str]] = typer.Option(
        platforms_env,
        "--platform", "-p", 
        help="List of platforms", 
        show_default=False
    ),
    countries: Optional[List[str]] = typer.Option(
        countries_env,
        "--country", "-c", 
        help="List of countries", 
        show_default=False
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
        run_pcaster(        
            storage_client_constructor=StorageClient,

            # Sink parameters
            container_name=container_name, 
            sink_dir=sink_dir,
            overwrite=overwrite,

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

            # Scraping parameters             
            sources=sources,
            platforms=platforms,
            countries=countries,

            # Sink parameters
            delay=delay,
            retries=retries
        )
    except Exception as e:
        typer.echo(f"An error occurred during the scraping process: {e}", err=True)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()

