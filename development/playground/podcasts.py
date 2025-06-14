import os
import pyarrow.parquet as pq
from storage_lib import StorageClient
from io import BytesIO
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# Number of top podcasts in the final ranking
TOP=7

s3_creds = {
    # -- Local S3 Storage --
    "s3_access_key": "your_access_key",
    "s3_secret_key": "your_secret_key",
    # "s3_endpoint_url": "http://host.docker.internal:8333", <-- for Dockerized applications
    "s3_endpoint_url": "http://localhost:8333", 
    "s3_use_ssl": False
}

# Initialize Storage Clients
s3_client = StorageClient(credentials=s3_creds)

# List S3 Containers
res = s3_client.list_containers()
print("List of S3 Containers:", res)

# syntax: whisperer/raw_podcasts_data/date=2025-06-11/top_podcasts.parquet
CONTAINER_NAME = "whisperer"
SINK_DIR = "raw_podcasts_data"
SINK_DATE = datetime.now().strftime("%Y-%m-%d")
PODCASTS_STORAGE_KEY = f"{SINK_DIR}/date={SINK_DATE}/top_podcasts.parquet"
RESULTS_STORAGE_KEY = f"{SINK_DIR}/date={SINK_DATE}/scrape_job_status.parquet"

# ---------------------------------------------------------
# Download the Parquet file from S3 into a BytesIO object 
# - check if the file exists - if not, raise an error
# - read the Parquet file into a PyArrow Table
# ---------------------------------------------------------

podcasts_bytesIO = s3_client.storage_client.download_object(
    container_name="whisperer", storage_key=PODCASTS_STORAGE_KEY,
)

results_bytesIO = s3_client.storage_client.download_object(
    container_name="whisperer", storage_key=RESULTS_STORAGE_KEY,
)
print("Download successful, reading Parquet file...")

# Read the Parquet file from BytesIO object into a PyArrow Table
table_p = pq.read_table(podcasts_bytesIO)
table_r = pq.read_table(podcasts_bytesIO)

# Convert the PyArrow Table to a Pandas DataFrame
df = table_p.to_pandas()  

# Process the results DataFrame -- debug
print("Top Podcasts DataFrame (First 5 rows):")
print(df.head(5)) 



# ------------------------------------------------------------------
# 1 Normalize the 'itunes_id' column to ensure consistent data types
# ------------------------------------------------------------------

print("\nDataFrame Shape for itunes_id column:")

are_mixed_types: bool = df['itunes_id'].apply(type).nunique() > 1

if are_mixed_types or df['itunes_id'].dtype != 'string':
    """
    If the 'itunes_id' column contains mixed types,
    we normalize it to a string type to ensure consistency.
    """
    print(
        "Types in 'itunes_id' column:", 
        # NOTE: lambda returns type names instead of type objects
        df['itunes_id'].apply(lambda x: type(x).__name__).unique() 
    ) 
    print("Normalizing 'itunes_id' column to string type...")
    # NOTE: handle NaN values and convert to empty string
    df['itunes_id'] = df['itunes_id'].fillna('').astype(str) 
else:
    print("All values in 'itunes_id' are of the same type:", df['itunes_id'].dtype)

# ------------------------------------------------------------------
# 2 Enrich the DataFrame with 'itunes_id' missing values and episodes
#   using APIs: podcasting index, itunes
#   - get list of episodes for each podcast for given date with URL to audio
#   --> maybe some historical data ??
# ------------------------------------------------------------------


# type_counts = df['itunes_id'].apply(type).value_counts()
# print(type_counts)

# df_filtered = df[(df['itunes_id'] == "") | (df['itunes_id'].isnull())]

# print("\nFiltered DataFrame (Podcasts without iTunes ID):")
# print(df_filtered.count())


# ------------------------------------------------------------------
# 3 Group by 'source', 'platform' and 'country' 
#   and filter lists of TOP podcasts
# ------------------------------------------------------------------


# ----------------------------------------------------------
# 4. Use Borda Count to rank podcasts across groups [PL, US]
#    - Calculate average rank of podcasts across groups
#    - create two rankings for each country
# ----------------------------------------------------------

# -------------------------------------------------------
# 5. From two rankings [PL, US] retrieve top Episodes
#   - filter top episodes to get TOP episodes number for transcription
# -------------------------------------------------------

# ----------------------------------------------------
# 6. Save the results to S3 as Parquet files adn JSON batch file for Whisperer
#   - podcasts DataFrame
#   - results DataFrame
#   - batch.json file for Whisperer
# ----------------------------------------------------


# # Group by 'source', 'platform' and 'country' and count the number of podcasts
# grouped_df = df.groupby(['source', 'platform', 'country'])

# # Display count of podcasts in each group
# print("\nGrouped DataFrame (Count of Podcasts):")
# print(grouped_df.size().reset_index(name='podcast_count')) # [100 rows x 9 columns]

# # Display first 5 rows for each group
# print("\nDisplaying first 5 rows for each group:")
# for name, group in grouped_df:
#     print(f"\nGroup: {name}")
#     print(group.head(5))  # Display first 5 rows of each group