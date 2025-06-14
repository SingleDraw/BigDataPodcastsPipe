
from rapidfuzz import fuzz
import pandas as pd
from src.apis.i_tunes_api import ITunesAPI
from src.apis.podcast_index_api import PodcastIndexAPI
from src.ranker_tools.normalize_title import normalize_title
from typing import Optional

class PodcastApiManager:
    """
    A class to manage podcast APIs for fetching episodes and filling missing podcast IDs in a DataFrame.
    It provides methods to normalize podcast titles and compare them using fuzzy matching.
    """
    def __init__(
            self,
            itunes_api: ITunesAPI,
            podcasting_index_api: PodcastIndexAPI
        ):
        """
        Initialize the PodcastApiManager class.
        """
        self.itunes_api = itunes_api
        self.podcasting_index_api = podcasting_index_api
        self.normalize_title = normalize_title  # Use the imported normalize_title function



    def get_episodes_by_podcast_id(
            self,
            id: str,
            since: int,
            limit: int = 5,  # Limit the number of episodes to fetch
            podcast_api_id: str = "itunes_id"  # Column name for podcast ID in the DataFrame
        ) -> list[dict]:
        """
        Get episodes for a given podcast ID using the ITunesAPI or PodcastIndexAPI.
        Returns a list of episodes as dictionaries.
        """
        api_list = self.api_list

        # Check which API to use based on the podcast_api_id
        if podcast_api_id not in [key for _, key in api_list]:
            raise ValueError(f"Unknown podcast column ID: {podcast_api_id}")
        
        # Get the API instance based on the podcast_column_id
        for api, podcast_id_column_key in api_list:
            if podcast_api_id == podcast_id_column_key:
                break
        
        if not api:
            raise ValueError(f"API not found for podcast column ID: {podcast_api_id}")

        return api.get_episodes_by_podcast_id(
            id=id, 
            since=since, 
            limit=limit
        )



    def fill_missing_podcast_ids(
            self,
            df: pd.DataFrame,
            title_column_name: str = "podcast_title", # clustered_title
            podcasts_limit: int = 3,
            threshold: int = 90
        ) -> pd.DataFrame:
        """
        Fill missing podcast IDs in the DataFrame by searching for podcasts using APIs.
        This method iterates over the DataFrame, checks for missing podcast IDs, and searches for podcasts using the APIs.
        It uses fuzzy matching to compare podcast titles and find the best match.
        Returns the updated DataFrame with filled podcast IDs.
        """

        for api, podcast_id_column_key in self.api_list:   
            print(f"Using API: {api.__class__.__name__}")

            # Create a mask for podcasts with missing itunes_id
            missing_id_mask = df[podcast_id_column_key].eq("")

            for idx, row in df[missing_id_mask].iterrows():
                podcats_title = row[title_column_name]

                # Search for podcasts using the API,
                # limit the number of results to avoid excessive API calls
                found_podcasts = api.search_podcast(
                    search_term=podcats_title,
                    limit=podcasts_limit
                )
                

                print(f"Found {len(found_podcasts)} podcasts for search term '{podcats_title}':")
                
                
                # Check if any of the found podcasts match the title
                # - uses fuzzy matching method to compare titles
                best_title, podcast_id = self._compare_titles(
                    original_title=podcats_title, 
                    found_podcasts=[
                        (podcast.get("title", ""), podcast.get("id", "")) for podcast in found_podcasts],
                    threshold=threshold
                )

                if best_title is None:
                    # No match found, continue to the next podcast
                    continue

                # condition
                title_match = df[title_column_name] == podcats_title

                # found rows - avoids repeated matches
                if not title_match.any():
                    # No match found in the DataFrame, continue to the next podcast
                    continue

                row_idx = df.index[title_match]

                # Update the DataFrame with the found podcast id
                if (
                    row_idx is not None 
                    and len(row_idx) > 0 
                    and df.loc[row_idx, podcast_id_column_key].eq("").any()
                ):
                    df.loc[row_idx, podcast_id_column_key] = str(podcast_id)

        return df

    @property
    def api_list(
            self
        ) -> list[tuple[ITunesAPI | PodcastIndexAPI, str]]:
        """
        Get a list of APIs to use for podcast search.
        Returns a list of tuples with API instance and the key for podcast ID.
        """
        return [
            (self.itunes_api, "itunes_id"),
            (self.podcasting_index_api, "podcasting_index_id")
        ]

    def _compare_titles(
            self,
            original_title: str, 
            found_podcasts: list[tuple[str,str]], # list of tuples with (title, podcast_id) pairs
            threshold: int = 90                   # similarity threshold for matching - default is 90
        ) -> tuple[str, str] | None:
        """
        Compare two podcast titles using fuzzy matching.
        Returns the best matching title and its podcast_id if similarity exceeds the threshold.
        If no match is found, returns None.

        - Fuzzy matching is a must here, cause scraped titles can be slightly different than API retrieved ones.

        params:

        original_title - title from scraped dataset
        found_podcasts - list of tuples with titles found from api search terms and podcast_ids
        threshold      - percentage of similarity that must be achieved for acknownledging match

        """
        # list of tuples with (title, podcast_id, similarity)
        matched_titles: list[tuple[str,str,int]] = [] 

        for found_title, podcast_id in found_podcasts:
            similarity = fuzz.ratio(
                self.normalize_title(original_title), 
                self.normalize_title(found_title)
            )
            if similarity > threshold:
                # print(f"Matched '{original_title}' with '{found_title}' (similarity: {similarity})")
                matched_titles.append((found_title, podcast_id, similarity))

        # get the best match
        if matched_titles:
            # Get the tuple with the highest similarity score
            best_match = max(matched_titles, key=lambda x: x[2])  

            print(f"Best match for '{original_title}': '{best_match[0]}' with similarity {best_match[2]}")
            
            # Return the title and podcast_id of the best match
            return best_match[0], best_match[1]  
        else:
            print(f"No match found for '{original_title}'")
            return None, None
