import pandas as pd
from typing import Optional
from app.src.logger import logger
from app.src.ranker_tools.normalize_title import normalize_title
from app.src.ranker_tools.fuzzy_clusterer import FuzzyClusterer

# Display 6 decimal places for floats in DataFrame
pd.set_option("display.float_format", "{:.6f}".format)


class RankingFrame(pd.DataFrame):
    normalize_title = staticmethod(normalize_title)

    allowed_countries = [
        'us', 'pl'
    ]

    required_columns = [
        'source', 'platform', 'country', 'sort_by', 
        'rank', 'podcast_title', 'scraped_at', 
        'itunes_id', 'podcasting_index_id', 
        'borda_score'
    ]

    """
    Custom DataFrame class for Podcast Rankings.
    This class extends the Pandas DataFrame to represent a ranking frame
    """

    def __init__(
            self, 
            *args, 
            top: int = 10,  # Default to top 10 podcasts
            **kwargs
        ):
        super().__init__(*args, **kwargs)
        self.top = top  # Store the number of top podcasts to consider
        
    @property
    def _constructor(
            self
        ):
        """
        Override the constructor to ensure that the custom class is used
        when creating a new DataFrame from this class.
        """
        return RankingFrame
    

    def _validate_fields(
            self
        ) -> 'RankingFrame':
        """
        Validate that the DataFrame contains all required fields.
        Raises an error if any required field is missing.
        """
        logger.info("Validating fields in RankingFrame...")
        for col in self.required_columns:
            if col not in self.columns:
                raise ValueError(f"Missing required column: {col}")
        return self


    def __finalize__(
            self, 
            previous_self, 
            method=None, 
            **kwargs
        ):
        """ Finalize the DataFrame after operations.
        This method ensures that the top attribute is preserved and fields are validated.
        """
        result = super().__finalize__(previous_self, method=method, **kwargs)
        if isinstance(previous_self, RankingFrame):
            result.top = getattr(previous_self, 'top', None)
        if method == 'from_dataframe':
            result = result._validate_fields()
        return result
    
    

    @staticmethod
    def from_dataframe(
            df: pd.DataFrame,
            top: int = 10,          # Default to top 10 podcasts
            threshold: int = 80     # Default threshold for clustering titles
        ) -> 'RankingFrame':
        """
        Static factory method to convert a DataFrame into a RankingFrame.
        """
        if not isinstance(df, pd.DataFrame):
            raise ValueError("Input must be a Pandas DataFrame.")
        if not isinstance(top, int) or top <= 0:
            raise ValueError("Top must be a positive integer.")
        if not isinstance(threshold, int) or not (0 <= threshold <= 100):
            raise ValueError("Threshold must be an integer between 0 and 100.")
        
        if 'podcasting_index_id' not in df.columns:
            df["podcasting_index_id"] = ""

        # add borda score column
        if 'borda_score' not in df.columns and 'rank' in df.columns:
            df['borda_score'] = top + 1 - df['rank']

        # Ensure 'normalized_title' column exists and has normalized titles
        if 'normalized_title' not in df.columns and 'podcast_title' in df.columns:
            df['normalized_title'] = df['podcast_title'].apply(
                lambda x: RankingFrame.normalize_title(x) if isinstance(x, str) else x
            )

        if 'clustered_title' not in df.columns and 'normalized_title' in df.columns:
            fuzz_clusterer = (
                FuzzyClusterer(
                    threshold=threshold,
                )
                .clusterize(
                    phrases=df['normalized_title'].tolist()
                )
                .get_inverted_mapping()
            )

            df['clustered_title'] = fuzz_clusterer.map_phrases(
                df, 
                source_column_name='normalized_title', 
                clustered_column_name='clustered_title'
            )['clustered_title']
            

        return RankingFrame(
            df.values, 
            columns=df.columns, 
            index=df.index,
            top=top
        ).__finalize__(df, method='from_dataframe')
    


    def filter_by_genre(
            self,
            genre: str | list[str] = 'top_podcasts'
        ) -> 'RankingFrame':
        if isinstance(genre, str):
            genre = [genre]

        elif not genre:
            # If genre is empty 
            # set wildcard to include all genres
            genre = ['*']

        elif not (
            isinstance(genre, list) 
            or 
            all(isinstance(g, str) for g in genre)
        ):
            raise ValueError(
                "Genre must be a string, "
                "list of strings, or '*' to include all genres."
            )

        # Handle wildcard genre
        if '*' in genre:
            return self

        # Filter the DataFrame by the specified genre(s)
        return self[
            self['sort_by'].isin(genre)
        ].__finalize__(self)



    def filter_by_country(
            self, 
            country: str
        ) -> 'RankingFrame':
        if not isinstance(country, str):
            raise ValueError("Country must be a string.")
        if country not in self.allowed_countries:
            raise ValueError(
                f"Country must be one of {self.allowed_countries}. "
                f"Provided country: {country}"
            )
        
        country = country.strip().lower()  # Normalize country input
        return self[self['country'] == country].__finalize__(self)

    

    def filter_top_ranked(
            self, 
            top_n: Optional[int] = None
        ) -> 'RankingFrame':
        top = top_n if top_n is not None else self.top

        if not isinstance(top, int) or top <= 0:
            raise ValueError(
                "Top N must be a positive integer. "
                f"Provided value: {top}"
            )
        
        # get the smallest group size
        grouped = self.groupby(['country', 'source', 'platform', 'sort_by'])['rank']
        min_group_size = grouped.size().min()
        if top > min_group_size:
            # raise ValueError(
            #     f"Top N ({top}) exceeds the minimum group size ({min_group_size}). "
            #     "Please choose a smaller value."
            # )
            top = min_group_size
            logger.warning(
                f"Adjusting top N to {top} based on the smallest group size ({min_group_size})."
            )
        else:
            logger.info(
                f"Filtering top {top} ranked podcasts per group where the smallest group size is {min_group_size}."
            )

        return self[
            # leave less than or equal to top N ranked podcasts per group
            self.groupby(['country', 'source', 'platform', 'sort_by'])['rank']
                .transform(lambda x: x <= top)  # Keep only the top N ranked podcasts
        ].__finalize__(self)
    


    def calculate_source_weights(
            self
        ) -> 'RankingFrame':
        """
        Calculate source weights based on the number of platforms available for each source.
        This method adds a 'source_weight' column to the DataFrame.
        """
        df = self.copy()
        df['source_weight'] = 1

        ### Naive approach to calculate source weights
        ### - it assumes that all rankings lists are equal length (and that all sources are equally important)
        ### - it works if filtering top N podcasts is done before this step

        # get number of platforms for each [source, sort_by, and country] group combination
        platform_counts = (
            df
                .groupby(['platform', 'sort_by', 'country'])['source']  # Get platform/sort_by/country grouped data
                .nunique()                                              # Count unique sources for each group
                .reset_index(name='platform_count')                     # Reset index to get a DataFrame from the groupby operation
        )

        # Merge the platform counts back into the original DataFrame - we get platform count for each [platform, sort_by, country] group
        # but it doesnt handle missing rows when list is shorter than other lists (sources) for same group
        
        df = df.merge(
            platform_counts,                        # Merge the platform counts back into the original DataFrame
            on=['platform', 'sort_by', 'country'],  # Match on platform, sort_by, and country key (group from above)
            how='left'                              # Use left join to keep all original rows                       
        )

        df['source_weight'] /= df['platform_count'] 

        df.drop(columns=['platform_count'], inplace=True)

        return RankingFrame.from_dataframe(
            df, 
            top=self.top
        ).__finalize__(self, method='calculate_source_weights')
        


    def apply_source_weights(
            self
        ) -> 'RankingFrame':
        """
        Apply source weights to the borda scores.
        This method modifies the 'borda_score' column based on the 'source_weight'.
        """
        if 'source_weight' not in self.columns:
            raise ValueError(
                "Source weights have not been calculated. "
                "Please call calculate_source_weights() first."
            )
        df = self.copy()
        df['borda_score'] *= df['source_weight']

        # Drop the 'source_weight' column as it's no longer needed
        df.drop(columns=['source_weight'], inplace=True)

        result_df = RankingFrame.from_dataframe(
            df, 
            top=self.top
        ).__finalize__(self, method='apply_source_weights')

        result_df.drop(
            columns=['source_weight'], 
            inplace=True, 
            errors='ignore'
        ) # Drop 'source_weight' if it exists

        return result_df
    


    def normalize_borda_scores(
            self
        ) -> 'RankingFrame':
        """
        Normalize the borda scores within each group of country, source, platform, and sort_by.
        This method modifies the 'borda_score' column to be normalized.
        """
        df = self.copy()
        _max_borda_value = df.max()['borda_score']
        _min_borda_value = df.min()['borda_score']
        _borda_range = _max_borda_value - _min_borda_value

        def ___normalize_fn(x: float) -> float:
            if _borda_range == 0:
                return 0
            return (x - _min_borda_value) / _borda_range
        
        df['borda_score'] = df['borda_score'].apply(___normalize_fn)

        return RankingFrame.from_dataframe(
            df, 
            top=self.top
        ).__finalize__(self, method='normalize_borda_scores')
    


    def group_by_titles(
            self
        ) -> 'RankingFrame':
        """        Group the DataFrame by 'clustered_title' and aggregate the results.
        This method returns a DataFrame with the aggregated results.
        """

        df = self.copy()
        if 'clustered_title' not in df.columns:
            raise ValueError("The DataFrame must contain 'clustered_title' column to group by titles.")
        
        def __aggregate_values(x):
            """
            Aggregate IDs, keeping unique values and filtering out empty strings.
            """
            return list(filter(None, x.dropna().str.strip().unique()))
        
        def __sum_and_round(x, precision=6):
            """
            Sum the values and round them to 2 decimal places.
            """
            return round(x.sum(), precision)
        

        ### df['aggregated_rows'] = df.groupby('clustered_title')['podcast_title'].transform('count')

        # Group by 'clustered_title' and aggregate the results
        grouped_df = (
            df
                .groupby('clustered_title')
                .agg({
                    # 'aggregated_rows': lambda x: list(x),  # Keep all aggregated rows
                    'podcast_title': 'first',  # Keep the first podcast title
                    'source': 'first', # __aggregate_values,  # Keep all unique sources
                    'platform': __aggregate_values,  # Keep all unique platforms
                    'country': __aggregate_values,  # Keep all unique countries
                    'sort_by': __aggregate_values,  # Keep all unique sort_by values
                    'rank': 'mean',  # Average the ranks
                    'borda_score': __sum_and_round,  # We sum the borda scores and round them due to floating point imprecision
                    'scraped_at': 'max',  # Get the latest scraped_at date
                    # Keep all unique values for these columns
                    'itunes_id': 'first', # __aggregate_values,
                    'podcasting_index_id': 'first' # __aggregate_values
                })
                .sort_values(
                    by=['borda_score', 'rank'],
                    ascending=[False, True]  # Sort by borda_score descending and rank ascending
                ).reset_index()
        )

        return RankingFrame.from_dataframe(
            grouped_df, 
            top=self.top
        ).__finalize__(self, method='group_by_titles')

