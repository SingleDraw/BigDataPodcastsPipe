import datetime
from app.src.podcast_scraper import PlaywrightPodcastScraper
from app.src.logging_config import logger
from app.src.helpers import retry_upload
from typing import Literal, Dict, Optional
from io import BytesIO
import json

"""
Podcast Metadata Provider App
"""

class PCaster:
    scraper_constructor = PlaywrightPodcastScraper

    def __init__(
            self, 
            overwrite: bool = False,
            container_name: str = "whisperer",
            sink_dir: str = "raw_podcasts_data",
            storage_client_constructor = None,
            storage_credentials: dict = None,
            retries: int = 3,
            delay: int = 1,
            filters: Dict[Literal["sources", "platforms", "countries"], Optional[str]] = None
        ):
        """
        Main configuration class for the Podcast Rankings App."""
        self.valid = True # flag for chain breaking
        self.overwrite = overwrite
        
        # Get the current date in UTC
        self._now = datetime.datetime.now(datetime.UTC)

        today = self._now.strftime("%Y-%m-%d")
        # today_iso_str = self._now.isoformat()

        """
        Results dictionary to store the results of the scraping process."""
        self.scraped = {
            "top_podcasts": None,
            "scrape_job_status": None
        }

        self.filters = {
            "sources":    filters.get("sources", None) if filters else None,    # all sources
            "platforms":  filters.get("platforms", None) if filters else None,  # all platforms
            "countries":  filters.get("countries", None) if filters else None   # all countries
        }

        """
        Sink configuration for Azure Blob Storage. """
        # 🧠 Validation only
        if not storage_client_constructor:
            raise ValueError("Storage client constructor is required.")
        
        self.storage_client_constructor = storage_client_constructor
        self.storage_credentials = storage_credentials
        self.storage_client = None
        self.container_name = container_name
        self.podcasts_blob_path = f"{sink_dir}/date={today}/top_podcasts.parquet"
        self.results_blob_path = f"{sink_dir}/date={today}/scrape_job_status.parquet"
        self.latest_blob_path = f"{sink_dir}/latest.json"

        """
        Runner for retry upload logic (curred)."""
        self.runner = retry_upload(
            retries=retries,
            delay=delay
        )

        self._set_client()


    def _check_existing_blobs(
            self
        ) -> None:
        """        
        Run the podcast scraping process."""
        if not self.storage_client:
            raise ValueError("Storage client is not set.")

        if self.overwrite:
            logger.warning(
                "Overwrite flag is set. Will overwrite existing blobs if they exist:"
                f"\nPodcasts Blob Path: {self.container_name}/{self.podcasts_blob_path}"
                f"\nResults Blob Path: {self.container_name}/{self.results_blob_path}"
            )
        if (
            self.storage_client.key_exists(
                container_name = self.container_name, 
                storage_key = self.podcasts_blob_path
            ) and 
            self.storage_client.key_exists(
                container_name = self.container_name, 
                storage_key = self.results_blob_path
            )
        ):
            if self.overwrite:
                logger.warning(
                    "Overwrite flag is set. Will overwrite existing blobs."
                )
                return
            else:
                logger.error(
                    "Blobs already exist and overwrite flag is not set. "
                    "Exiting to avoid overwriting existing data."
                )
                self.valid = False
            return
        
        logger.info("No existing blobs found.")
        return

    def scrape(
            self
        ) -> "PCaster":
        """
        Scrape podcasts and upload results to Azure Blob Storage."""

        self._check_existing_blobs()    

        if not self.valid:
            logger.error("Invalid state. Cannot proceed with scraping.")
            return self
        
        logger.info("Proceeding with scraping.")

        podcast_scraper = self.scraper_constructor(
            sources     =  self.filters.get("sources", None),
            platforms   =  self.filters.get("platforms", None),
            countries   =  self.filters.get("countries", None),
        )

        df_top_podcasts, df_scrape_results = podcast_scraper.scrape_podcasts()

        # Check if the DataFrames are empty
        if df_top_podcasts.empty:
            logger.error("No podcasts scraped. Exiting.")
            self.valid = False
            return self
        
        if df_scrape_results.empty:
            logger.error("No scrape results. Exiting.")
            self.valid = False
            return self
        
        self.scraped["top_podcasts"] = df_top_podcasts
        self.scraped["scrape_job_status"] = df_scrape_results

        logger.info("Successfully scraped podcasts.")

        return self

    def _set_client(
            self,
        ) -> None:
        """Set the storage client for uploading results."""
        if not self.valid:
            logger.error("Invalid state. Cannot upload results.")
            return self
        
        self.storage_client = self.storage_client_constructor(
            credentials=self.storage_credentials
        )


    def upload_results(
            self
        ) -> "PCaster":
        """
        Upload scraped results to Azure Blob Storage."""
        if not self.storage_client:
            raise ValueError("Storage client is not set. Cannot upload results.")

        if not self.valid:
            logger.error("Invalid state. Cannot upload results.")
            return self
        
        # Use the runner to upload DataFrames with retry logic
        self.runner(
            self.storage_client.upload_df_as_parquet,
            container_name=self.container_name,
            storage_key=self.podcasts_blob_path,
            df=self.scraped["top_podcasts"]
        )
        self.runner(
            self.storage_client.upload_df_as_parquet,
            container_name=self.container_name,
            storage_key=self.results_blob_path,
            df=self.scraped["scrape_job_status"]
        )

        # Write the latest metadata to a JSON file
        self.runner(
            self.storage_client.upload_timestamp,
            container_name=self.container_name,
            storage_key=self.latest_blob_path,
            utc_time=self._now,
            overwrite=True
        )

        logger.info(
            f"Successfully uploaded DataFrames to Azure Blob Storage:\n"
            f"Podcasts Blob Path: {self.container_name}/{self.podcasts_blob_path}\n"
            f"Results Blob Path: {self.container_name}/{self.results_blob_path}"
        )

        return self

    def finalize(
            self,
            raise_on_invalid: bool = False
        ):
        if not self.valid and raise_on_invalid:
            raise ValueError("Validation failed during processing chain.")
        return self
