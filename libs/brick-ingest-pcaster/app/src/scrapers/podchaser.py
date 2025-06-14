import time
import pandas as pd
from app.src.logging_config import logger
from app.src.scrapers.abstract import AbstractScraper
from typing import Literal

"""
Playwright Scrapper for Podchaser Charts 
[https://www.podchaser.com/charts]

"""

class PodchaserScraper(AbstractScraper):
    base_url = "https://www.podchaser.com/charts"
    platforms = ["apple", "spotify"]
    countries = ["us", "pl"]
    genres = ["top_podcasts", "news"] # "business", "science", "technology"

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
        Scrapes the top podcasts from Podchaser charts.
        """

        source = "podchaser"
        results, job_id, scrape_date, job_result = self._create_job_entry(
            results, source, sort_by, country_code, platform
        )

        try: 
            context, page = self._load_page(
                goto_url=f"{self.base_url}/{platform}/{country_code}/{sort_by.replace('_', '%20')}?date={time.strftime('%Y-%m-%d')}",
                wait_for_selector="table tr"
            )

            # Get table rows
            rows = page.query_selector_all("table tr")

            logger.info("Scraping Podchaser charts...")

            rank = 1
            for row in rows:
                """
                The structure of the row is as follows:
                <a data-testid="podcastTitle" href="..." class="...">
                    <span>
                        <span>
                            Title
                        </span>
                    </span>
                </a>
                """
                title_element = row.query_selector("td:nth-child(2) a[data-testid='podcastTitle']")

                if title_element:
                    title = title_element.inner_text()
                    # link = title_element.get_attribute("href")

                    # podcasts DataFrame
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
            logger.error(f"Error scraping Podchaser charts: {e}")

        finally:
            # update the job result in the results DataFrame
            results.at[job_id, "status"] = job_result

        
        return df, results