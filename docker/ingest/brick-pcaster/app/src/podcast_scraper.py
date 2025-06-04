import pandas as pd
from playwright.sync_api import sync_playwright
from app.src.scrapers.podchaser import PodchaserScraper
from app.src.scrapers.apple import ApplePodcastsScraper
from app.src.scrapers.rephonic import RephonicScraper
from typing import Literal

_sources = {
    "podchaser": PodchaserScraper,
    "apple_podcasts": ApplePodcastsScraper,
    "rephonic": RephonicScraper
}
_platforms = ["apple", "spotify"]
_countries = ["us", "pl"]  



class PlaywrightPodcastScraper:
    """
    Playwright Podcast Scraper
    Uses Playwright to scrape data from Podchaser, Apple Podcasts, and Rephonic.
    """

    def __init__(
            self,
            sources:    list[Literal["podchaser", "apple_podcasts", "rephonic"]]    = None, # all sources
            platforms:  list[Literal["apple", "spotify"]]                           = None, # all platforms
            countries:  list[Literal["us", "pl"]]                                   = None # all countries
        ):
        """
        Initialize the PlaywrightPodcastScraper instance.
        """
        self.sources = [ s for s in sources if s in _sources.keys() ] if sources else list(_sources.keys())
        self.platforms = [ p for p in platforms if p in _platforms ] if platforms else None
        self.countries = [ c for c in countries if c in _countries ] if countries else None

    def get_dataframes(
            self
        ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Returns the DataFrames used for scraping.
        """
        # DataFrame to store the top podcasts
        df_top_podcasts = pd.DataFrame(columns=[
            "job_id",           # unique identifier for the scrape job = results index
            "source",           # scraper source, e.g. "podchaser", "apple_podcasts",
            "platform",         # platform for which ranking is scraped, e.g. "apple", "spotify"
            "country",          # country code, e.g. "us", "pl"
            "sort_by",          # sorting criteria, e.g. "top_podcasts", or genre like "news", "business", etc.
            "rank",             # rank of the podcast in the chart, e.g. 1, 2, 3, ...
            "podcast_title",    # title of the podcast
            "scraped_at",       # timestamp when the data was scraped
            "itunes_id"         # podcast id, may be empty - needs to be provided later (or added podcasting index id in another column)
        ])

        # DataFrame to store scrape job results
        df_scrape_results = pd.DataFrame(columns=[
            "source",       # scraper source, e.g. "podchaser", "apple_podcasts", "rephonic"
            "platform",     # platform for which ranking is scraped, e.g. "apple", "spotify"
            "country",      # country code, e.g. "us", "pl"
            "sort_by",      # sorting criteria, e.g. "top_podcasts", or genre like "news", "business", etc.
            "scraped_at",   # timestamp when the data was scraped
            "status"        # status of the scrape job, "success" or "failed"
        ])

        return df_top_podcasts, df_scrape_results


    def scrape_podcasts(
            self
        ) -> None:
        """
        Scrape top podcasts from various sources using Playwright.
        This method initializes the Playwright browser, creates instances of the scrapers,
        and iterates through them to scrape the data.
        It also handles the DataFrames for top podcasts and scrape results.
        """

        # Get the DataFrames for top podcasts and scrape results
        df_top_podcasts, df_scrape_results = self.get_dataframes()

        # 1 Scrape all top podcasts from various sources
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True, 
                # 221 milliseconds delay between actions 
                # to avoid potential rate limiting
                slow_mo=221 
            ) 

            # Initialize scrapers with the browser instance and specified filters
            scrapers = [
                _sources[source](
                    browser=browser, 
                    platforms=self.platforms, 
                    countries=self.countries
                )
                for source in self.sources
            ]

            # Scrape data from all available sources
            for scraper in scrapers:
                df_top_podcasts, df_scrape_results = scraper.scrape_all(
                    df=df_top_podcasts,
                    results=df_scrape_results
                )

            # Cast itunes_id to string type
            # This is necessary for consistency, as some IDs may be numeric
            df_top_podcasts["itunes_id"] = df_top_podcasts["itunes_id"].astype(str)

            # Convert DataFrames to appropriate dtypes
            df_top_podcasts = df_top_podcasts.convert_dtypes()
            df_scrape_results = df_scrape_results.convert_dtypes()

            browser.close() # Close the browser after scraping


        return df_top_podcasts, df_scrape_results