from __future__ import annotations
from io import BytesIO
# from pandas import DataFrame # Saving space a bit
from storage_lib.utils.logger import logger
from typing import Any

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
except ImportError as e:
    pa = None
    pq = None


def parquet_writes(cls):
    """
    Decorator to add methods for uploading pd.DataFrames as Parquet files to Azure Blob Storage.
    This decorator adds a method to the class that allows uploading a DataFrame as a Parquet file.
    """
    def upload_df_as_parquet(
            self, 
            storage_key: str, 
            df: "DataFrame", # type hint for pandas DataFrame
            container_name: str, 
            overwrite: bool = True
        ) -> None:
        """
        Write a DataFrame to a Parquet file in Azure Blob Storage.
        """
        if pa is None or pq is None:
            raise ImportError(
                "pyarrow is required for Parquet support. "
                "Install with `pip install /path-to/violet-storage-lib[parquet]`."
            )
        try:
            table = pa.Table.from_pandas(df)
            buffer = BytesIO()
            pq.write_table(table, buffer)
            buffer.seek(0)
        except Exception as e:
            logger.error(f"Error converting DataFrame to Parquet: {e}")
            raise

        self.upload_object(
            storage_key=storage_key, 
            source=buffer, 
            container_name=container_name, 
            overwrite=overwrite
        )

    # Attach new methods to the class
    cls.upload_df_as_parquet = upload_df_as_parquet
    cls.upload_df_as_parquet.__doc__ = (
        "Write a DataFrame to a Parquet file in Azure Blob Storage."
    )

    return cls
