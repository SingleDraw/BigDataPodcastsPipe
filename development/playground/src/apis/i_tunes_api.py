import requests
from src.apis.abstract import AbstractApi
from src.helpers import itunes_date_to_timestamp
from src.types import PodcastType, EpisodeType
from typing import Optional

class ITunesAPI(AbstractApi):
    def __init__(
            self,    
            base_url: str = "https://itunes.apple.com",
            date_to_timestamp = itunes_date_to_timestamp
        ):
        self.base_url = base_url
        self.date_to_timestamp = date_to_timestamp

    def _request(
            self, 
            endpoint: str,
            params: dict = None
        ) -> dict:
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    

    def search_podcast(
            self, 
            search_term: str,
            limit: int = 6
        ) -> list["PodcastType"]:

        params = {
            "term": search_term,
            "entity": "podcast",
            "limit": str(limit)
        }
        podcasts = self._request("search", params).get("results", [])

        return [
            {
                "source": "itunes_api",
                "id": podcast.get("collectionId", ""),
                "title": podcast.get("collectionName", ""),
                "categories": podcast.get("genres", [])
            } for podcast in podcasts
        ]


    def get_episodes_by_podcast_id(
            self, 
            id: str,
            since: Optional[int] = None,
            limit: int = 5
        ) -> list["EpisodeType"]:

        params = {
            "id": id,
            "entity": "podcastEpisode",
            "sort": "recent"
        }

        if limit is not None and isinstance(limit, int):
            """
            Validate the limit parameter.
            iTunes API allows a maximum of 3000 results.
            """
            if limit < 1 or limit > 3000:
                raise ValueError("Limit must be between 1 and 3000")
            params["limit"] = str(limit)

        data = self._request("lookup", params).get("results", [])

        if since is not None:
            """
            iTunes API does not support filtering episodes 
            by a specific date or timestamp.
            Results must be filtered manually after fetching.
            """
            data = [
                episode for episode in data 
                if "releaseDate" in episode and 
                self.date_to_timestamp(episode["releaseDate"]) >= since
            ]

        return [
            {
                "id": episode.get("trackId", ""),
                "title": episode.get("trackName", ""),
                "release_date": self.date_to_timestamp(episode.get("releaseDate", "")),
                "duration": round(episode.get("trackTimeMillis", 0) / 1000),    # Convert milliseconds to seconds
                "transcription": None,                                          # iTunes API does not provide transcripts
                "audio_source": episode.get("trackViewUrl", "")
            } for episode in data
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
            "entity": "podcastEpisode",
            "limit": str(limit),
            "sort": "recent"
        }
        data = self._request("search", params).get("results", [])

        if since is not None:
            """
            iTunes API does not support filtering episodes 
            by a specific date or timestamp.
            Results must be filtered manually after fetching.
            """
            data = [
                episode for episode in data 
                if "releaseDate" in episode and 
                self.date_to_timestamp(episode["releaseDate"]) >= since
            ]
            
        return [
            {
                "id": episode.get("trackId", ""),
                "title": episode.get("trackName", ""),
                "release_date": self.date_to_timestamp(episode.get("releaseDate", "")),
                "duration": round(episode.get("trackTimeMillis", 0) / 1000),  # Convert milliseconds to seconds
                "transcription": None,  # iTunes API does not provide transcripts
                "audio_source": episode.get("trackViewUrl", "")
            } for episode in data
        ]