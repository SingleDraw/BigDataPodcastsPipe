import time
from datetime import datetime
from typing import Optional


# Retry decorator function for handling upload retries
def retry_upload(
        retries=5, 
        delay=1
    ) -> callable:
    def wrapper(
            func: callable,
            *args,
            **kwargs
        ) -> Optional[any]:
        d = delay
        for i in range(retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if i < retries - 1:
                    time.sleep(d)
                    d *= 2
                else:
                    raise e
    return wrapper
            


# Helper functions for date and time formatting
# Convert a timestamp to a human-readable date string
# date helper
def format_date(
        timestamp: int | float | str
    ) -> str:
    """Format a timestamp into a human-readable date."""
    try:
        timestamp = int(timestamp)
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        return "Invalid timestamp"



# Convert a date string to a timestamp
# iTunes date helper
def itunes_date_to_timestamp(
        date_str: str # e.g., "2023-10-01T12:34:56Z"
    ) -> Optional[int]:
    """Convert iTunes date string to timestamp."""
    try:
        # Replace 'Z' with '+00:00' for UTC timezone
        normalized_date_str = date_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized_date_str)
        return int(dt.timestamp())
    except ValueError:
        return None