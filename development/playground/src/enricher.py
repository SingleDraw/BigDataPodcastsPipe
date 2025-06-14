import dotenv, datetime, time
import json
import pandas as pd
from storage_lib import StorageClient
from src.api_manager import PodcastApiManager
from src.ranker_tools.ranking_frame import RankingFrame
from typing import Optional
from src.logger import logger
from src.config import (
    CONTAINER_NAME,
    TARGET_JOBS_STORAGE_KEY,
    TARGET_LATEST_STORAGE_KEY,
    TRANSCRIPTION_DIR
)
dotenv.load_dotenv()



class Enricher:
    default_params = {
        "top": 10,  # Default to top 10 podcasts
        "countries": ["us", "pl"],  # Default to US podcasts
        "title_clustering_threshold": 80,  # Similarity threshold for fuzzy matching
        "filter_genre": "*",  # Filter for 'top_podcasts' by default
        "master_limit": 50,  # Limit the DataFrame to the top N podcasts
        "podcasts_api_search_limit": 50,  # Limit for the number of podcasts to search for missing IDs
        "podcast_title_search_threshold": 90,  # Threshold for fuzzy matching of podcast titles when searching for podcasts in APIs
        "episodes_fetch_limit_per_podcast": 5,  # Limit for the number of episodes urls to fetch per podcast
    }

    def __init__(
        self, 
        df: pd.DataFrame,
        api_manager: PodcastApiManager,
        enrichment_params: dict
    ):
        self.df = df
        self.api_manager = api_manager
        self.enrichment_params = self._validate_params(
            enrichment_params
        )
        self.master_ranking: Optional[dict[str, RankingFrame]] = {}
        self.master_episodes: Optional[dict[str, pd.DataFrame]] = {}
        self.batch_job_json = None  # Placeholder for batch job JSON



    # FUTURE IMPROVEMENT:
    # 1. Add a method to get paths with parametrized date 
    #    instead of hardcoded one from config module
    def save_results( 
            self,
            storage_client: StorageClient,
            raise_on_missing_batch_job: bool = True,
            verbose: bool = True
        ) -> 'Enricher':
        """
        Save the enriched master ranking and episodes DataFrames to the storage.
        """
        if raise_on_missing_batch_job and self.batch_job_json is None:
            raise ValueError(
                "Batch job JSON is not generated. "
                "Please call generate_batch_job_json() before saving results."
            )

        # Save master ranking DataFrame
        for country, master_ranking in self.master_ranking.items():
            storage_client.upload_df_as_parquet(
                df=master_ranking,
                container_name=CONTAINER_NAME,
                storage_key=f"{TARGET_JOBS_STORAGE_KEY}/{country}/master_ranking.parquet"
            )
            if verbose:
                logger.info(f"Master ranking for {country}:\n")
                logger.info(self.preview_df(master_ranking, n=5))
                logger.info(f"Master ranking for {country} uploaded successfully.")

        # Save master episodes DataFrame
        for country, df_episodes in self.master_episodes.items():
            storage_client.upload_df_as_parquet(
                df=df_episodes,
                container_name=CONTAINER_NAME,
                storage_key=f"{TARGET_JOBS_STORAGE_KEY}/{country}/master_episodes.parquet"
            )
            if verbose:
                logger.info(f"Master episodes for {country}:\n")
                logger.info(self.preview_df(df_episodes, n=5))
                logger.info(f"Master episodes for {country} uploaded successfully.")

        # Save batch job JSON if it exists
        if self.batch_job_json is not None:
            # upload the batch job JSON twice, for metadata:
            storage_client.upload_json(
                data=self.batch_job_json,
                container_name=CONTAINER_NAME,
                storage_key=f"{TARGET_JOBS_STORAGE_KEY}/batch_job.json"
            )
            # and as a separate file for the transcription jobs source
            # this one will be overwritten by the next batch job
            storage_client.upload_json(
                data=self.batch_job_json,
                container_name=CONTAINER_NAME,
                storage_key=f"batch_job.json"
            )
            if verbose:
                logger.info("Batch job JSON generated and uploaded successfully.")
                logger.info(f"Batch job JSON:\n{json.dumps(self.batch_job_json, indent=2)}")


        # Write latest stamp to the storage
        storage_client.upload_timestamp(
            container_name=CONTAINER_NAME,
            storage_key=TARGET_LATEST_STORAGE_KEY,
            utc_time=datetime.datetime.now(datetime.UTC),
            overwrite=True
        )

        return self

    def preview_df(
            self,
            df: pd.DataFrame,
            n: int = 5
        ) -> pd.DataFrame:
        """
        Preview the first n rows of a DataFrame.
        """
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame.")
        if not isinstance(n, int) or n <= 0:
            raise ValueError("n must be a positive integer.")
        return df.head(n) if not df.empty else pd.DataFrame(columns=df.columns)


    def generate_batch_job_json(
            self,
            jobs_limit: int = 3,        # Limit the number of jobs per country in the batch job JSON
            round_robin: bool = True    # Whether to use round-robin distribution of borda scores 

        ) -> 'Enricher':
        """
        Generate a batch job JSON file for whisperer transcription and upload it to the storage.
        """
        # Validate the jobs_limit parameter
        if not isinstance(jobs_limit, int) or jobs_limit <= 0:
            raise ValueError("jobs_limit must be a positive integer.")
        if not isinstance(round_robin, bool):
            raise TypeError("round_robin must be a boolean value.")

        # Initialize the batch job JSON list
        batch_job_json = []
        today = datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%d')
        idx = 0
        target_storage_name = 'default'  # Default storage name for the output path
        target_protocol = "s3"  # Default protocol for the output path
        target_prefix = f"{target_storage_name}+{target_protocol}"  # Default prefix for the output path
        target_path = lambda c, idx: f"{target_prefix}://{CONTAINER_NAME}/{TRANSCRIPTION_DIR}/date={today}/country={c}/{idx}.txt"

        # Iterate over each country in the master ranking
        for country, df_episodes in self.master_episodes.items():
            # Create a copy of the DataFrame for processing
            df = df_episodes.copy()  

            if round_robin:
                # Sort episodes by podcast_id, borda_score descending, and rank ascending
                df = (
                    df
                    .sort_values(
                        by=['podcast_id', 'borda_score', 'rank'], 
                        ascending=[True, False, True]
                    )
                    .reset_index(drop=True)
                )
                # Group by 'podcast_id' and assign a position based on the order within each group
                # the order is determined by the sorting above and reflect borda_score and rank
                # cumcount() starting from + 1 assigns a position to each episode within its podcast_id group
                # This ensures that episodes are processed in a round-robin fashion across podcasts
                df['position'] = (
                    df
                    .groupby('podcast_id', sort=False) # respect the current order of podcast_id
                    .cumcount() + 1  # Assign a position based on the order within each podcast_id
                )
                # Sort the DataFrame by 'position', 'borda_score' descending, and 'rank' ascending
                # Restore index after sorting
                df = (
                    df
                    .sort_values( 
                        by=['position', 'borda_score', 'rank'],
                        ascending=[True, False, True]
                    )
                    .reset_index(drop=True)
                )

            # Iterate over each episode in the DataFrame
            job_per_country = 0

            for _, row in df.iterrows():

                job_per_country += 1

                # Create a job entry for each episode
                job_entry = {

                    # Input and output paths for the transcription job
                    "input": row['audio_source'], 
                    "output": target_path(country, idx),  

                    # Episode metadata
                    "country": country,
                    "podcast_title": row['podcast_title'],
                    "podcast_clustered_title": row['podcast_clustered_title'],
                    "podcast_api_id": row['podcast_api_id'],
                    "podcast_id": row['podcast_id'],
                    "rank": row['rank'],
                    "borda_score": row['borda_score'],
                    "scraped_at": row['scraped_at'],
                    "fetched_at": row['fetched_at'],
                    "episode_id": row['episode_id'],
                    "episode_title": row['episode_title'],
                    "release_date": row['release_date'],
                    "duration": row['duration']
                }
                batch_job_json.append(job_entry)
                idx += 1  # Increment the index for the next job entry

                # Limit the number of jobs in the batch job JSON
                if job_per_country >= jobs_limit:
                   break



        # Save the batch job JSON to the instance variable
        self.batch_job_json = batch_job_json

        return self



    def run_pipelines(
            self,
        ) -> 'Enricher':
        
        self.run_master_rankings_pipelines()  # Run master rankings pipelines for each country
        self.run_episodes_pipelines()  # Run episodes enrichment pipelines for each podcast in each master ranking
        return self
    


    def run_master_rankings_pipelines(
            self,
        ) -> 'Enricher':
        """
        Run the master ranking pipelines for each country specified in enrichment_params.
        """
        podcasts_api_search_limit = self.enrichment_params.get(
            "podcasts_api_search_limit"
        )
        podcast_title_search_threshold = self.enrichment_params.get(
            "podcast_title_search_threshold"
        )
        
        # Run the master ranking pipeline for each country
        for country in self.enrichment_params["countries"]:
            # Create the master ranking for the country
            master_ranking = (
                self.api_manager
                    # Fill missing podcast IDs in the master ranking
                    .fill_missing_podcast_ids(
                        # Get Master Ranking DataFrame
                        df=self._create_master_ranking(
                            country=country
                        ),
                        title_column_name="podcast_title",  # clustered_title       # search by
                        podcasts_limit=podcasts_api_search_limit, 
                        threshold=podcast_title_search_threshold
                    ).sort_values(
                        # Sort the DataFrame by 'borda_score' in descending order
                        'borda_score', 
                        ascending=False
                    ).pipe(
                        # Filter out podcasts with empty IDs
                        lambda df: df[(df['itunes_id'] != "") & (df['podcasting_index_id'] != "")]
                    ).reset_index(
                        drop=True
                    )
            )

            self.master_ranking[country] = master_ranking
        
        return self
        


    def run_episodes_pipelines(
            self,
        ) -> 'Enricher':
        """
        Run the episodes enrichment pipelines 
        for each podcast 
        in each master ranking.
        """
        episodes_fetch_limit_per_podcast = self.enrichment_params.get(
            "episodes_fetch_limit_per_podcast"
        )
        since_date_fetch = self.enrichment_params.get(
            "since_date_fetch"
        )

        # Initialize the DataFrame for episodes
        df_episodes = pd.DataFrame(
            columns=[
                # Country metadata
                'country',
                # Podcast metadata
                'podcast_title', 'podcast_clustered_title', 
                'podcast_api_id', 'podcast_id', 
                'rank', 'borda_score', 'scraped_at', 
                # Episode metadata
                'fetched_at', 'episode_id', 'episode_title',
                'release_date', 'duration', 
                'transcription', 'audio_source'
            ]
        ) 

        # Iterate over each country in the master ranking
        for country, master_ranking in self.master_ranking.items():
            for _, row in master_ranking.iterrows():


                # Get the podcast ID from the row
                podcast_api_id = 'podcasting_index_id'
                podcast_id = row.get(podcast_api_id)
                if not podcast_id:
                    podcast_api_id = 'itunes_id'
                    podcast_id = row.get(podcast_api_id)
                if not podcast_id:
                    podcast_id = None
                    continue

                # Podcast metadata for each row
                podcast_clustered_title, podcast_title = row.get('clustered_title', None), row.get('podcast_title')
                rank, borda_score, scraped_at = row.get('rank'), row.get('borda_score'), row.get('scraped_at')
                            

                # Fetch episodes for each podcast in the master ranking
                episodes = self.api_manager.get_episodes_by_podcast_id(
                    id=podcast_id,
                    since=since_date_fetch,
                    limit=episodes_fetch_limit_per_podcast,
                    podcast_api_id=podcast_api_id
                )

                fetched_at = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

                # Process each episode and append to the DataFrame
                if episodes:
                    new_episodes_rows=[{
                        'country': country,
                        'podcast_title': podcast_title,
                        'podcast_clustered_title': podcast_clustered_title,
                        'podcast_api_id': podcast_api_id,
                        'podcast_id': podcast_id,
                        'rank': rank,
                        'borda_score': borda_score,
                        'scraped_at': scraped_at,  # Timestamp when the podcast was scraped
                        'fetched_at': fetched_at,
                        'episode_id': episode.get('id', ''),
                        'episode_title': episode.get('title', ''),
                        'release_date': episode.get('release_date', ''),
                        'duration': episode.get('duration', 0),  # Duration in seconds
                        'transcription': episode.get('transcription', None),  # Transcription URL or text
                        'audio_source': episode.get('audio_source', '') if str(episode.get('audio_source', '')).endswith(('.mp3', '.m4a', '.wav')) or any(x in str(episode.get('audio_source', '')) for x in ['.mp3?', '.wav?', '.m4a?']) else None
                    } for episode in episodes]

                    df_new_episodes = pd.DataFrame(new_episodes_rows)

                    # Append new episodes to the DataFrame
                    df_episodes = pd.concat(
                        [df_episodes, df_new_episodes],
                        ignore_index=True
                    )

            # Add dataframe to the dictionary with country as key
            # ordered by 'borda_score' descending, rank ascending
            df_episodes = (
                df_episodes
                    .sort_values(
                        by=['borda_score', 'rank'], 
                        ascending=[False, True]
                    )
                    .reset_index(drop=True)  # Reset index after sorting
            )
            # Reset index to ensure it is clean
            self.master_episodes[country] = df_episodes

        return self



    def _create_master_ranking(
            self,
            country: str = "us",
    ) -> 'RankingFrame':
        """
        Create the master ranking for a given country.
        This method processes the DataFrame to create a RankingFrame with enriched podcast data.
        """
        return (
            RankingFrame
                # Convert DataFrame to RankingFrame 
                .from_dataframe(
                    # DataFrame with podcast metadata                    
                    self.df,   
                    # Number of top podcasts limit per ranking for processing purposes                             
                    top=self.enrichment_params["top"],     
                    # Similarity threshold for fuzzy matching                  
                    threshold=self.enrichment_params["title_clustering_threshold"],  
                )    
                .filter_by_genre(
                    # Filter for 'top_podcasts' by default, or use '*'/None as wildcard for all genres
                    genre=self.enrichment_params["filter_genre"]
                )              
                # Filter by country, default is 'us'  
                .filter_by_country(country=country)   
                .filter_top_ranked()            # Filter to top N=TOP ranked podcasts - defines processing scope
                .calculate_source_weights()     # Calculate source weights based on platforms
                .apply_source_weights()         # Apply source weights to borda scores
                .group_by_titles()              # Group by podcast titles
                .normalize_borda_scores()       # Normalize borda scores
                .head(self.enrichment_params["master_limit"])  # Limit the DataFrame to the top N podcasts           
        )




    def _validate_params(
            self,
            enrichment_params: dict
        ) -> dict:
        """
        Validate and set default values for enrichment parameters.
        """
        # iterate over default_params and check their types
        for key, value in self.default_params.items():
            if key not in enrichment_params:
                # if not provided in enrichment_params, set default value
                enrichment_params[key] = value
            else:
                # # if provided, ensure it's of the correct type
                for t in [int, str, list]:
                    if isinstance(value, t) and not isinstance(enrichment_params[key], t):
                        raise TypeError(
                            f"Parameter '{key}' should be of type {t.__name__}, "
                            f"got {type(enrichment_params[key]).__name__} instead."
                        )
                
        # handle 'since_date_fetch' parameter
        # if not provided, set it to 1 day ago
        if "since_date_fetch" not in enrichment_params:
            last_day = int(round(datetime.datetime.now().timestamp() - 60 * 60 * 24)) # 1 day ago               
            enrichment_params["since_date_fetch"] = last_day
        else:
            if not isinstance(enrichment_params["since_date_fetch"], int):
                raise TypeError(
                    "Parameter 'since_date_fetch' should be of type int."
                )

        # Ensure 'countries' is a list of strings
        if not isinstance(enrichment_params["countries"], list) or not all(isinstance(country, str) for country in enrichment_params["countries"]):
            raise TypeError(
                "Parameter 'countries' should be a list of strings."
            )

        return enrichment_params