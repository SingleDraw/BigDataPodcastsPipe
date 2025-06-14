
from typing import Optional
from src.types import PodcastType, EpisodeType

class AbstractApi:
    """
    Abstract class for API implementations.
    This class defines the basic structure and methods that any API class should implement.
    """

    def __init__(
            self
        ):
        """
        Initialize the API instance.
        This method can be overridden by subclasses to set up specific configurations.
        """
        pass

    def search_podcast(
            self, 
            search_term: str,
            limit: int = 6
        ) -> list["PodcastType"]:
        """
        Search for podcasts by term.
        :param search_term: The term to search for.
        :param limit: The maximum number of results to return.
        :return: List of podcasts matching the search term.
        """
        raise NotImplementedError("This method should be overridden by subclasses.")
    
    def get_episodes_by_podcast_id(
            self, 
            id: str,
            since: Optional[int] = None,
            limit: int = 5
        ) -> list["EpisodeType"]:
        """
        Get episodes by podcast ID.
        :param id: The ID of the podcast.
        :param since: Optional timestamp to filter episodes.
        :param limit: The maximum number of episodes to return.
        :return: List of episodes for the specified podcast.
        """
        raise NotImplementedError("This method should be overridden by subclasses.")