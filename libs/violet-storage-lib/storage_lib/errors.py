class StorageDownloadError(Exception):
    """Exception raised when there is an error downloading a file from storage."""
    pass

class StorageUploadError(Exception):
    """Exception raised when there is an error uploading a file to storage."""
    pass