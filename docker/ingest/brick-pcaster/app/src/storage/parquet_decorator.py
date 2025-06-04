from io import BytesIO
from pandas import DataFrame
import pyarrow as pa
import pyarrow.parquet as pq
from app.src.logging_config import logger
from typing import Optional


def parquet_writes(cls):
    """
    Decorator to add methods for uploading pd.DataFrames as Parquet files to Azure Blob Storage.
    This decorator adds a method to the class that allows uploading a DataFrame as a Parquet file.
    """
    def upload_df_as_parquet(
            self, 
            blob_path: str, 
            df: DataFrame,
            container_name: Optional[str], 
            overwrite: bool = True
        ) -> None:
        """
        Write a DataFrame to a Parquet file in Azure Blob Storage.
        """
        try:
            table = pa.Table.from_pandas(df)
            buffer = BytesIO()
            pq.write_table(table, buffer)
            buffer.seek(0)
        except Exception as e:
            logger.error(f"Error converting DataFrame to Parquet: {e}")
            raise

        self.upload_blob(
            blob_path=blob_path, 
            data=buffer, 
            container_name=container_name, 
            overwrite=overwrite
        )

    # Attach new methods to the class
    cls.upload_df_as_parquet = upload_df_as_parquet
    cls.upload_df_as_parquet.__doc__ = (
        "Write a DataFrame to a Parquet file in Azure Blob Storage."
    )

    return cls
