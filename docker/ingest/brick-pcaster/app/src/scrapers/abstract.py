
import pandas as pd
import time, random
from typing import Literal

class AbstractScraper:
    """
    Abstract base class for scrapers.
    All scrapers should inherit from this class 
    and implement the `scrape` method.
    """
    base_url: str = ""
    platforms: list[str] = []
    countries: list[str] = []
    genres: list[str] = []


    def __init__(
            self, 
            browser,
            platforms: list[str] = None,
            countries: list[str] = None,
        ):
        """
        Initialize the scraper instance.
        :param browser: The browser instance to use for scraping.
        """
        if browser is None:
            raise ValueError(
                "Browser instance must be provided."
            )
        self.browser = browser

        # All available if None
        self.available_platforms = platforms
        self.available_countries = countries



    def scrape(
            self,
            df: pd.DataFrame,
            results: pd.DataFrame,
            country_code: Literal["pl", "us"] = "us",
            sort_by: Literal[ 
                "top_podcasts", "business", "news", "science", "technology"
            ] = "top_podcasts",
            platform: Literal["apple", "spotify"] = "apple"
        ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Scrape data from a source.
        This method should be implemented by subclasses.
        :param df: DataFrame to store the scraped data.
        :param results: DataFrame to store the scrape job results.
        :param country_code: Country code for the data to be scraped.
        :param sort_by: Sorting criteria for the data to be scraped.
        :param platform: Platform for which the data is being scraped.
        :return: Tuple of DataFrames (df, results).
        :raises NotImplementedError: If the method is not implemented in a subclass.
        """
        raise NotImplementedError(
            "Subclasses must implement the scrape method."
        )
    


    def scrape_all(
            self,
            df: pd.DataFrame,
            results: pd.DataFrame
        ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Scrape data from all sources.
        This method can be used to scrape data from multiple sources.
        Override this method in subclasses if iteration logic is different.
        :param df: DataFrame to store the scraped data.
        :param results: DataFrame to store the scrape job results.
        :return: Tuple of DataFrames (df, results).
        """
        for platform in self.platforms if self.available_platforms is None else self.available_platforms:
            for country in self.countries if self.available_countries is None else self.available_countries:
                for genre in self.genres:
                    # Introduce a random delay to avoid rate limiting
                    # This adds a delay between 0.0 and 0.4 seconds
                    time.sleep(random.uniform(0.2, 0.5))
                    df, results = self.scrape(
                        df=df,
                        results=results,
                        country_code=country,
                        sort_by=genre,
                        platform=platform
                    )
                    
        return df, results
    

    
    def _create_job_entry(
            self,
            results: pd.DataFrame,
            source: str,
            sort_by: str,
            country_code: str,
            platform: str,
            scrape_date: str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),
            job_result: str = 'failed'
        ) -> tuple:
        """        Creates a new job entry in the results DataFrame.
        """
        # 1. Append a new job to the results DataFrame
        results = results._append({
            "source": source,
            "sort_by": sort_by,
            "country": country_code,
            "platform": platform,
            "scraped_at": scrape_date,
            "status": job_result
        }, ignore_index=True)
        # 2. Get index of that job
        job_id = results.index[-1]
        return results, job_id, scrape_date, job_result
    


    def _get_context_and_page(self):
        """
        Creates a new browser context and page with a specific user agent.
        This method is used to ensure that each scrape starts with a fresh context.
        """
        context = self.browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/116.0.0.0 Safari/537.36"
            )
        )

        # ✅ Create a fresh page for each scrape
        page = context.new_page()

        return context, page
    

        
    def _load_page(
            self,
            goto_url: str,
            wait_for_selector: str,
            wait_until: str = "networkidle",
            timeout: int = 10000
        ):
        """ Loads a page and waits for a specific selector to be visible.
        """
        context, page = self._get_context_and_page()
        page.goto(goto_url, wait_until=wait_until)
        page.wait_for_selector(wait_for_selector, timeout=timeout)
        return context, page