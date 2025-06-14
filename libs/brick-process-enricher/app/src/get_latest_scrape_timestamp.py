import datetime
from storage_lib import StorageClient
from app.src.logger import logger

def get_latest_scrape_timestamp(
        storage_client: StorageClient,
        container_name: str,
        storage_key: str,
        fallback_range_days: int = 2  # Days to look back if latest date isn't available
    ) -> int:

    # 1. read latest.json file from Azure Blob Storage 
    # to get the last scraped date
    try:
        # latest_json = data_provider.get_json_from_storage(
        latest_json = storage_client.download_json(
            storage_key=storage_key,
            container_name=container_name
        )
    except Exception as e:
        logger.error(f"Error fetching latest.json from Azure Blob Storage: {e}")
        latest_json = None

    # 3. if latest_json is available, use the date from it
    if latest_json and "ISO_date" in latest_json:
        latest_scrape_date = latest_json["ISO_date"]
    else:
        logger.warning("No valid latest date found, using fallback date.")
        latest_scrape_date = datetime.datetime.fromtimestamp(
            datetime.datetime.now(
                tz=datetime.timezone.utc  # Ensure we use UTC for consistency
            ).timestamp() - (fallback_range_days * 24 * 60 * 60)
        ).isoformat()

    last_scrape_timestamp = datetime.datetime.fromisoformat(
        latest_scrape_date
    ).timestamp()  # Convert to timestamp

    logger.info(f"Using latest scrape date: {latest_scrape_date}")

    return int(last_scrape_timestamp)  # Return as an integer timestamp
