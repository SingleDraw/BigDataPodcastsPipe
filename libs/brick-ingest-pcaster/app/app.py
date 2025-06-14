from app.src.logging_config import logger
from app.src.pcaster import PCaster
from typing import List, Optional

def run_pcaster(
        storage_client_constructor,
        azure_storage_account: str,
        azure_storage_key: str = "",

        s3_access_key: str = "",
        s3_secret_key: str = "",
        s3_endpoint_url: str = "",
        s3_use_ssl: Optional[bool] = None,
        s3_region_name: str = "",

        # Sink parameters
        overwrite: bool = False,
        container_name: str = "",  
        sink_dir: str = "",

        # Scraping parameters
        sources: Optional[List[str]] = None,
        platforms: Optional[List[str]] = None,
        countries: Optional[List[str]] = None,
        
        # Retry parameters
        delay: int = 1,     # Delay in seconds between retries
        retries: int = 3    # Number of retries for storage upload failures
    ):
    try:
        kwargs = {
            "overwrite": overwrite,
            "storage_client_constructor": storage_client_constructor,
            "storage_credentials": {
                "azure_storage_account": azure_storage_account,
                "azure_storage_key": azure_storage_key,
                "s3_access_key": s3_access_key,
                "s3_secret_key": s3_secret_key,
                "s3_endpoint_url": s3_endpoint_url,
                "s3_use_ssl": s3_use_ssl,
                "s3_region_name": s3_region_name
            },
            "container_name": container_name,
            "sink_dir": sink_dir,
            "retries": retries,
            "delay": delay,
            "filters": {
                "sources": sources,
                "platforms": platforms,
                "countries": countries
            }
        }

        # Initialize and run the PCaster
        _ = (
            PCaster(**kwargs)
            .scrape()
            .upload_results()
            .finalize()
        )
    except Exception as e:
        logger.error(f"An error occurred during the scraping process: {e}")
        raise



if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--overwrite", 
        action="store_true", 
        help="Overwrite existing data in the storage"
    )
    args = parser.parse_args()
    run_pcaster(overwrite=args.overwrite)

