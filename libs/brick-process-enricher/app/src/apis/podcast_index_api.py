import requests
import time
import hashlib
from app.src.apis.abstract import AbstractApi
from app.src.types import PodcastType, EpisodeType
from typing import Optional

class PodcastIndexAPI(AbstractApi):
    def __init__(
            self, 
            api_key: str,
            api_secret: str,
            base_url: str = "https://api.podcastindex.org/api/1.0"
        ):
        if not api_key or not api_secret:
            raise ValueError("Missing API credentials for Podcast Index")
        
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url



    def _request(
            self,
            endpoint: str,
            params: Optional[dict] = None
        ) -> dict:

        # Generate headers for the request
        epoch_time_string = str(int(time.time()))
        data_to_hash = self.api_key + self.api_secret + epoch_time_string
        sha_1 = hashlib.sha1(data_to_hash.encode('utf-8')).hexdigest()

        headers = {
            "X-Auth-Date": epoch_time_string,
            "X-Auth-Key": self.api_key,
            "Authorization": sha_1,
            "User-Agent": "PodcastIdeaGenerator/0.1",
        }

        response = requests.get(
            url=f"{self.base_url}/{endpoint}",
            headers=headers, 
            params=params
        )

        response.raise_for_status()

        return response.json()



    def search_podcast(
            self,
            search_term: str,
            limit: int = 6
        ) -> list["PodcastType"]:

        data = self._request(
            endpoint="search/byterm", 
            params={
                "q": search_term,
                "max": str(limit),
                "fulltext": "true"
            }
        )

        return [
            {
                "source": "podcast_index_api",
                "id": podcast.get("id", ""),
                "title": podcast.get("title", ""),
                "categories": [category for category in (podcast.get("categories") or {}).values()],
            } for podcast in data.get("feeds", [])
        ]        



    def get_episodes_by_podcast_id(
            self, 
            id: int,
            limit: Optional[int],  # Limit the number of episodes to fetch
            since: Optional[int],  # Timestamp to fetch episodes since
        ) -> list["EpisodeType"]:

        params = {
            "id": id,           # Podcast ID to fetch episodes for
            "start": "0",       # Start from the first episode
            "fulltext": "true"  # Include full text search - by default text is truncated to 100 characters
        }

        if limit is not None and isinstance(limit, int):
            if limit < 1 or limit > 3000:
                limit = max(1, min(limit, 3000))
            params["max"] = str(limit)
        else:
            params["max"] = "10"

        if since is not None and isinstance(since, int):
            params["since"] = since

        data = self._request("episodes/byfeedid", params)

        return [
            {
                "id": episode.get("id", ""),
                "title": episode.get("title", ""),
                "release_date": episode.get("datePublished", ""),
                "duration": episode.get("duration", 0),
                "transcription": episode.get("transcriptUrl", ""),  # URL to the transcript of the episode
                "audio_source": episode.get("enclosureUrl", ""),    # This is where the audio file is located
            } for episode in data.get("items", [])
        ]



    def get_recent_episodes(
            self, 
            since: Optional[int] = None,  # Timestamp to fetch episodes since
            limit: int = 5
        ) -> list["EpisodeType"]:
        """
        Get recent episodes across all podcasts.
        :param limit: The maximum number of recent episodes to return.
        :return: List of recent episodes.
        """
        params = {
            "max": str(limit),
            "fulltext": "true"
        }
        data = self._request("recent/episodes", params)

        if since is not None and isinstance(since, int):
            data["items"] = [
                episode for episode in data.get("items", [])
                if "datePublished" in episode and 
                episode["datePublished"] >= since
            ]

        return [
            {
                "feed_id": episode.get("feedId", ""),
                "feed_title": episode.get("feedTitle", ""),
                "id": episode.get("id", ""),
                "title": episode.get("title", ""),
                "release_date": episode.get("datePublished", ""),
                "duration": episode.get("duration", 0),
                "transcription": episode.get("transcriptUrl", ""),  # URL to the transcript of the episode
                "audio_source": episode.get("enclosureUrl", ""),    # This is where the audio file is located
            } for episode in data.get("items", [])
        ]