import pandas as pd
from app.src.logging_config import logger
from app.src.scrapers.abstract import AbstractScraper
from typing import Literal


class ApplePodcastsScraper(AbstractScraper):
    """
    Playwright Scraper for Apple Podcasts Charts
    [https://podcasts.apple.com/us/charts]
    """
    base_url = "https://podcasts.apple.com"
    platforms = ["apple"]
    countries = ["us", "pl"]
    genres = ["top_podcasts"]  # Apple Podcasts only has top podcasts


    def scrape(
            self,
            df: pd.DataFrame,
            results: pd.DataFrame,
            country_code: Literal["pl", "us"] = "us",
            sort_by: Literal[ 
                "top_podcasts"  # , "business", "news", "science", "technology"
            ] = "top_podcasts", # irrelevant for Apple Podcasts
            platform: Literal["apple"] = "apple"
        ):
        """
        Scrapes the top podcasts from Apple Podcasts charts.
        """

        source = "apple_podcasts"
        results, job_id, scrape_date, job_result = self._create_job_entry(
            results, source, sort_by, country_code, platform
        )

        try: 
            context, page = self._load_page(
                goto_url=f"{self.base_url}/{country_code}/charts",
                wait_for_selector="div[aria-label='Top Shows']"
            )

            # Get top shows titles
            """
            <div aria-label="Top Shows">
            <div class="shelf-content">
                <div>
                ...
                    <span 
                        data-testid="product-lockup-title"
                        > 
                        Title 
                    </span>
            """
            titles = page.query_selector_all(
                "div[aria-label='Top Shows'] span[data-testid='product-lockup-title']"
            )

            logger.info("Scraping Apple Podcasts charts...")

            rank = 1
            for title_element in titles:
                title = title_element.inner_text()

                df = df._append({
                    "job_id": job_id,
                    "source": source,
                    "rank": rank,
                    "sort_by": sort_by,
                    "country": country_code,
                    "itunes_id": "",  # Podchaser ID can be extracted from the link if needed
                    "podcast_title": title,
                    "platform": platform,
                    "scraped_at": scrape_date
                }, ignore_index=True)

                rank += 1

            page.close()  
            context.close()  
            job_result = 'success'

        except Exception as e:
            logger.error(f"Error scraping Apple Podcasts charts: {e}")

        finally:
            # update the job result in the results DataFrame
            results.at[job_id, "status"] = job_result


        return df, results