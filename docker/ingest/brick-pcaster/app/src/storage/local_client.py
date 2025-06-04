

import os
from io import BytesIO
from app.src.storage.parquet_decorator import parquet_writes


@parquet_writes
class LocalStorageClient:
    """
    A class to handle local storage for debugging purposes.
    It provides methods to save and retrieve data 
    in a local tmp directory as if it were in Azure Blob Storage.
    """

    def __init__(
            self,
            *args,
            **kwargs
        ):
        """
        Initialize the LocalStorageClient.
        This client is used for debugging purposes and does not connect to any remote storage.
        """
        pass

    def upload_blob(
            self, 
            blob_path: str, 
            data: BytesIO, 
            container_name: str = "debug",
            overwrite: bool = True
        ) -> None:
        """
        Save data to a local file for debugging.
        :param blob_path: The path where the data will be saved.
        :param data: The data to save.
        :param container_name: The name of the container (not used in local storage).
        :param overwrite: Whether to overwrite the file if it exists.
        """
        mode = 'wb' if overwrite else 'ab'
        # Ensure the directory exists
        full_blob_path = f"tmp/{container_name}/{blob_path}"
        os.makedirs(
            os.path.dirname(f"tmp/{container_name}/{blob_path}"),
            exist_ok=True
        )

        with open(full_blob_path, mode) as f:
            f.write(data.getvalue()) # gets the bytes from BytesIO


client = LocalStorageClient()