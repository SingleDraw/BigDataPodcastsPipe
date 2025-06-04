from app.src.logging_config import logger
from app.src.pcaster import PCaster
from typing import List, Optional

def run_pcaster(
        storage_client_constructor,
        azure_storage_account: str,
        azure_storage_key: str = "",
        overwrite: bool = False,
        sources: Optional[List[str]] = None,
        platforms: Optional[List[str]] = None,
        countries: Optional[List[str]] = None,
        delay: int = 1,     # Delay in seconds between retries
        retries: int = 3    # Number of retries for storage upload failures
    ):
    try:
        pcaster = (
            PCaster(
                overwrite=overwrite,
                storage_client_constructor=storage_client_constructor,
                storage_credentials={
                    "azure_storage_account": azure_storage_account,
                    "azure_storage_key": azure_storage_key
                },
                container_name = "whisperer",
                sink_dir = "raw_podcasts_data",
                retries = retries,
                delay = delay,
                filters={
                    "sources":   sources,
                    "platforms": platforms,
                    "countries": countries
                }
            )
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

