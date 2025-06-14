import time, random
import pandas as pd
from app.src.logging_config import logger
from app.src.scrapers.abstract import AbstractScraper
from typing import Literal
from app.src.utils import Validate

"""
PLaywright Scraper for Rephonic Charts
[https://rephonic.com/charts/spotify/united-states/top-podcasts]

"""

class RephonicScraper(AbstractScraper):
    base_url = "https://rephonic.com/charts"
    platforms = [
        "spotify", 
        "apple"
        # "youtube"  # Uncomment if you want to include YouTube in the future
    ] 
    countries = {
        "spotify" : [
            "us",
            "pl",
            # -- Add more countries as needed
            # "uk",  # United Kingdom
            # "de",  # Germany
            # "fr",  # France
            # "ca",  # Canada
            # "au",  # Australia
            # "in",  # India
            # "id",  # Indonesia
            # "jp",  # Japan
            # "br",  # Brazil
            # "mx",  # Mexico
            # "ar",  # Argentina
            # "cl",  # Chile
            # "co",  # Colombia
            # "it",  # Italy
            # "es",  # Spain
            # "nl",  # Netherlands
            # "ie",  # Ireland
            # "se",  # Sweden
            # "no",  # Norway
            # "at",  # Austria
            # "dk",  # Denmark
            # "fi",  # Finland
            # "nz",  # New Zealand
            # "ph",  # Philippines
        ],
        "apple" : [
            "us", 
            "pl",
            # -- Add more countries as needed
            # "ua",  # Ukraine
            # "de",  # Germany
            # "at",  # Austria
            # "ch",  # Switzerland
            # "gb",  # United Kingdom
            # "fr",  # France
            # "ca",  # Canada
            # "au",  # Australia
            # "in",  # India
            # "jp",  # Japan
            # "br",  # Brazil
            # "mx",  # Mexico
            # "it",  # Italy
            # "es",  # Spain
            # "ie",  # Ireland
            # "nl",  # Netherlands
            # "be",  # Belgium
            # "se",  # Sweden
            # "no",  # Norway
            # "fi",  # Finland
            # "dk",  # Denmark
            # "ru",  # Russia
            # "cn",  # China
            # "kr",  # South Korea
            # "za",  # South Africa
            # "ar",  # Argentina
            # "cl",  # Chile
            # "co",  # Colombia
            # "hk",  # Hong Kong
            # "tw",  # Taiwan
            # "ae",  # United Arab Emirates
            # "sa",  # Saudi Arabia
            # "nz",  # New Zealand
            # "sg",  # Singapore
            # "id",  # Indonesia
            # "ph",  # Philippines
            # "il",  # Israel
        ],
        "youtube" : [
            "us",
            "pl",
            # -- Add more countries as needed
            # "uk",  # United Kingdom
            # "ca",  # Canada
            # "fr",  # France
            # "de",  # Germany
            # "au",  # Australia
            # "it",  # Italy
            # "kr",  # South Korea
            # "hk",  # Hong Kong
            # "tw",  # Taiwan
            # "es",  # Spain
            # "ie",  # Ireland
            # "se",  # Sweden
            # "ch",  # Switzerland
            # "sg",  # Singapore
            # "no",  # Norway
            # "at",  # Austria
            # "dk",  # Denmark
            # "jp",  # Japan
            # "fi",  # Finland
            # "be",  # Belgium
            # "nl",  # Netherlands
            # "in",  # India
            # "id",  # Indonesia
            # "br",  # Brazil
            # "ru",  # Russia
            # "mx",  # Mexico
            # "ae",  # United Arab Emirates
            # "sa",  # Saudi Arabia
            # "il",  # Israel
            # "ar",  # Argentina
            # "cl",  # Chile
            # "co",  # Colombia
            # "nz",  # New Zealand
            # "ph",  # Philippines
            # "za",  # South Africa
            # "ua",  # Ukraine
        ]
    }
    genres = {
        "spotify": [
            "top_podcasts", 
            "trending",
            # -----------------
            # # not all genres are available for every country
            # "arts",
            # "business",
            # "comedy",
            # "education",
            # "fiction",
            # "health_&_fitness",
            # "history",
            # "leisure",
            # "music",
            # "news",
            # "religion_&_spirituality",
            # "science",
            # "society_&_culture",
            # "sports",
            # "technology",
            # "true_crime",
            # "tv_&_film"
        ],  
        "apple": [
            "top_podcasts",
            "news",
            # "government",
            # "technology",
            # "business",
            # "science",
            # "society_&_culture",
            # --------
            # "leisure",
            # "religion_&_spirituality",
            # "art",
            # "health_&_fitness",
            # "tv_&_film",
            # "education",
            # "kids_&_family",
            # "comedy",
            # "fiction",
            # "music",
            # "history",
            # "true_crime",
        ],
        "youtube": [
            "popular_podcasts",
        ]
    }

    # maps country codes to their full names for the URL
    country_names = {
        "us": "united-states",
        "pl": "poland",
        # "de": "germany",
    }

    def scrape_all(
            self,
            df: pd.DataFrame,
            results: pd.DataFrame
        ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Custom method to scrape all combinations of platforms, countries, and genres.
        """

        Validate.is_instance(
            df, pd.DataFrame, "df"
        )

        Validate.is_instance(
            results, pd.DataFrame, "results"
        )

        for platform in self.platforms:
            for country in self.countries[platform]:
                for genre in self.genres[platform]:
                    # Sleep to avoid being blocked by the website
                    time.sleep(random.uniform(0.2, 0.5))
                    df, results = self.scrape(
                        df=df,
                        results=results,
                        country_code=country,
                        sort_by=genre,
                        platform=platform
                    )
                    
        return df, results

    def scrape(
            self,
            df: pd.DataFrame,
            results: pd.DataFrame,
            country_code: Literal["pl", "us"] = "us",
            sort_by: Literal[ 
                "top_podcasts", "trending",
            ] = "top_podcasts",
            platform: Literal["spotify"] = "spotify"
        ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Scrapes the top podcasts from Podchaser charts.
        """

        source = "rephonic"
        results, job_id, scrape_date, job_result = self._create_job_entry(
            results, source, sort_by, country_code, platform
        )

        try: 
            # Construct the URL based on the platform, country, and genre
            genre_name = sort_by.replace("&_", "").replace("_", "-") 
            context, page = self._load_page(
                goto_url=f"{self.base_url}/{platform}/{self.country_names[country_code]}/{genre_name}",
                wait_for_selector="div[role='list']", # <-- don't touch it, it works this way, no questions asked
            )

            # # Get the page content for debugging
            # pc = page.content()
            # with open("tmp/debug_rephonic.html", "w", encoding="utf-8") as f:
            #     f.write(pc)            

            """
            The structure of the page is complex, so we need to navigate through it carefully.
            The main chart container is a script tag with id "__NEXT_DATA__" that contains JSON data.
            Example structure:
            <script id="__NEXT_DATA__" type="application/json">
                {
                    "props": {
                        "pageProps": {
                            "platformId":"spotify",
                            "countrySlug":"united-states",
                            "categoryId":"top-podcasts",
                            "podcasts":[
                                {
                                    "id":"the-joe-rogan-experience",
                                    "position":1,
                                    "change":0,
                                    "itunes_id":360084272,
                                    "name":"The Joe Rogan Experience",
                                    "guests":true,
                                    "sponsored":true,
                                    "publisher": {
                                        "id":"joe-rogan",
                                        "name":"Joe Rogan"
                                    },
                                    "artwork_url":"https://img.rephonic.com/artwork/the-joe-rogan-experience.jpg?width=600\u0026height=600\u0026quality=95",
                                    "artwork_thumbnail_url":"https://img.rephonic.com/artwork/the-joe-rogan-experience.jpg?width=70\u0026height=70\u0026quality=95",
                                    "key":"0-the-joe-rogan-experience"
                                }, 
                                ...
                            ]
                        }
                    }
                }
            </script>
            """

            # Get the main chart container
            next_script = page.query_selector("script#__NEXT_DATA__")
            if next_script:
                logger.info("Scraping Rephonic charts...")

                # Get the JSON data from the script tag
                json_data = next_script.inner_text()
                import json
                data = json.loads(json_data)

                # Extract the podcasts from the JSON data
                podcasts = data['props']['pageProps']['podcasts']

                rank = 1
                for podcast in podcasts:
                    title = podcast['name']
                    podcast_id = podcast['itunes_id']

                    # podcasts DataFrame
                    df = df._append({
                        "job_id": job_id,  # Add job_id to the DataFrame
                        "source": source,
                        "rank": rank,
                        "sort_by": sort_by,
                        "country": country_code,
                        "itunes_id": podcast_id,
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