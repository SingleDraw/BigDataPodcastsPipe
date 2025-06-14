from rapidfuzz import process, fuzz
import pandas as pd

"""
example usage:
from src.ranker_tools.fuzzy_compare import FuzzyClusterer

df = pd.DataFrame({
    'podcast_title': ['apple podcast', 'apple podcasts', 'apple podcasting', 'apple podcaster']
})

clusterer = (
    FuzzyClusterer(threshold=80)
        .clusterize(df['podcast_title'].tolist())
        .get_inverted_mapping()
        .map_phrases(df, source_column_name='podcast_title', clustered_column_name='clustered_title')
)

"""

class FuzzyClusterer:
    """
    A class to cluster phrases based on fuzzy matching.
    It uses the RapidFuzz library to compute similarity scores between phrases.
    """
    def __init__(
            self, 
            threshold: int = 80             
        ):
        self.threshold = threshold                       # Similarity threshold for clustering
        self.assigned = set()                            # to avoid re-processing phrases already assigned to a clusters dictionary
        self.clusters: dict[str, list[str]] = {}         # clusters containing lists of phrases that are similar to each other.
        self.phrase_to_cluster_map: dict[str, str] = {}  # mapping of phrases to their cluster representatives


    def _init_cluster_key(
            self,
            phrase: str 
        ) -> None:
        """
        Initialize a cluster key for a given phrase.
        """
        if phrase not in self.clusters:
            self.clusters[phrase] = []


    def _get_similarity_matrix(
            self, 
            phrases: list[str],
            scorer=fuzz.token_sort_ratio # token_sort_ratio is recommended for phrase comparison
        ) -> list[list[int]]:
        """
        Compute the similarity matrix for the given phrases.
        """
        return process.cdist(
            phrases, 
            phrases, 
            scorer=scorer
        )
        

    def clusterize(
            self, 
            phrases: list[str]
        ) -> "FuzzyClusterer":

        """
        Cluster phrases based on fuzzy matching.
        This method iterates through the titles, computes their similarity scores,
        """

        # Compute similarity matrix
        similarities = self._get_similarity_matrix(phrases)
        
        for i, phrase in enumerate(phrases):
            if phrase in self.assigned:
                continue  # Skip already assigned phrases
            
            # Start a new cluster with the current phrase
            self._init_cluster_key(phrase)
            self.clusters[phrase].append(phrase)

            # Mark the current phrase as visited
            self.assigned.add(phrase)

            # Check all other phrases for similarity
            for j in range(i + 1, len(phrases)):
                if phrases[j] not in self.assigned and similarities[i][j] >= self.threshold:
                    self._init_cluster_key(phrases[j])
                    self.clusters[phrase].append(phrases[j])
                    self.assigned.add(phrases[j])

        return self


    def get_inverted_mapping(
            self
        ) -> "FuzzyClusterer":
        """
        Invert the clusters mapping to create a phrase to cluster mapping.
        """
        self.phrase_to_cluster_map = {}  # Reset the mapping
        
        # Go through each cluster
        for normalized_key_phrase, group in self.clusters.items():
            # and through each phrase in the cluster
            for phrase in group:
                # to use the original phrase as the key 
                # with assigned normalized phrase as value for mapping
                self.phrase_to_cluster_map[phrase] = normalized_key_phrase

        return self
    

    def map_phrases(
            self, 
            df: pd.DataFrame, 
            source_column_name: str = 'podcast_title',
            clustered_column_name: str = 'clustered_title'
        ) -> pd.DataFrame:
        """
        Map the original phrases in the DataFrame to their cluster representatives.
        """

        # Ensure the source column exists in the DataFrame
        if source_column_name not in df.columns:
            raise ValueError(f"Source column '{source_column_name}' not found in DataFrame.")
        
        # Ensure the phrase to cluster map is created
        if not self.phrase_to_cluster_map:
            raise ValueError("Phrase to cluster mapping is not initialized. Call 'get_inverted_mapping()' first.")
        
        # Ensure the clustered column name is not already in the DataFrame
        if clustered_column_name in df.columns:
            raise ValueError(f"Column '{clustered_column_name}' already exists in DataFrame. Choose a different name.")

        # Map the phrases in the DataFrame
        df[clustered_column_name] = df[source_column_name].map(
            # self.phrase_to_cluster_map
            lambda phrase: self.phrase_to_cluster_map.get(phrase, phrase)  # Use the original phrase if not found in the mapping
        )

        return df
