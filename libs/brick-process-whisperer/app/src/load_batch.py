import json
from pathlib import Path

"""
    Batch path syntax:
    --batch default+s3://whisper/batch.json
    Load the batch file and return its content as a list of jobs. format:
    [
        {
            "input": "default+s3://bucket/podcast_1.mp3",
            "output": "s3://bucket/output1.txt"
        },
        {
            "input": "customblob+s3://bucket/podcast_2.mp3",
            "output": "default+az://container/output2.txt"
        }
    ]
"""

def load_batch(
        batch_path: Path
    ) -> list:

    from app.src.storages import storages   # Storage client provider
    from app.src.utils import parse_conn_uri
    # io for buffered reading
    from io import BytesIO

    # Get Source Client based on the batch_path parsed URI
    conn_name, conn_type, storage_unit, key_path = parse_conn_uri(batch_path)

    # prepare buffer for response
    batch_data = BytesIO()
    
    if conn_type in ["http", "https"]:
        # Use requests library to download the file for HTTP(S) sources
        import requests
        url = f"{conn_type}://{storage_unit}/{key_path}"
        response = requests.get(url, stream=True)
        # parse the JSON content
        
        if response.status_code == 200:
            batch_data.write(response.content)
            batch_data.seek(0)
            jobs = json.load(batch_data)
            return jobs

    
    # Use the storage client to download the file
    storage = storages.get_client(
        name=conn_name,
        type=conn_type
    )

    # Download object with batch data from storage
    batch_data = storage.download_object(
        container_name=storage_unit,
        storage_key=key_path
    )

    batch_data.seek(0)
    jobs = json.load(batch_data)
    return jobs

