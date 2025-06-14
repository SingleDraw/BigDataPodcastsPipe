import os
import pyarrow.parquet as pq
from storage_lib import StorageClient
from io import BytesIO
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

az_creds = {
    # -- Remote Azure Blob Storage --
    "azure_storage_account": os.getenv("AZURE_STORAGE_ACCOUNT_NAME", ""),
    "azure_storage_key": os.getenv("AZURE_STORAGE_ACCOUNT_KEY", ""),
}

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
az_client = StorageClient(credentials=az_creds)

# List S3 Containers
res = s3_client.list_containers()
print("List of S3 Containers:", res)

# List Azure Containers
res = az_client.list_containers()
print("List of Azure Containers:", res)

#  whisperer/raw_podcasts_data/date=2025-06-11/top_podcasts.parquet
CONTAINER_NAME = "whisperer"
SINK_DIR = "raw_podcasts_data"
SINK_DATE = datetime.now().strftime("%Y-%m-%d")
STORAGE_KEY = f"{SINK_DIR}/date={SINK_DATE}/top_podcasts.parquet"

bytesIOres = s3_client.storage_client.download_object(
    container_name="whisperer",
    storage_key=STORAGE_KEY,
)
print("Download successful, reading Parquet file...")

# table = pq.read_table("data.parquet")
table = pq.read_table(bytesIOres)
df = table.to_pandas()  # optional: convert to pandas DataFrame
print(df.head(100))  # print first 10 rows of the DataFrame
