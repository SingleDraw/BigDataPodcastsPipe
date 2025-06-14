> Reusabe local library for unified interaction
with a storage (s3/blob/local filesystem)

```bash

# Standard installation:
pip install /path-to/violet-storage-lib

# With optional parquet support:
pip install /path-to/violet-storage-lib[parquet]

```
```python

# Imports in python scripts:

from storage_lib import (
    # Generic Clients
    StorageClient, 
    LocalStorageClient,
    # Specific CLients
    S3StorageClient,
    AzureBlobStorageClient,
    # Errors
    StorageDownloadError,
    StorageUploadError
)

```
