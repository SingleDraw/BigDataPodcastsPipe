import os
import time
from pathlib import Path
from typing import Optional

class Validate:
    """
    A utility class for validation methods.
    Provides static methods to validate various types of inputs.
    """

    @staticmethod
    def non_empty_string(
            value: str, 
            name: str
        ) -> None:
        """
        Validate that the given value is a non-empty string.
        Raises ValueError if the value is not a non-empty string.
        """
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a non-empty string")

    @staticmethod
    def is_instance(
            value: object, 
            expected_type: type, 
            name: str
        ) -> None:
        """
        Validate that the given value is an instance of the expected type.
        Raises TypeError if the value is not an instance of the expected type.
        """
        if not isinstance(value, expected_type):
            raise TypeError(f"{name} must be an instance of {expected_type.__name__}")
        

def parse_conn_uri(
        uri: str,
        allow_http: bool = True
    ) -> tuple[str, str, str, str]:
    """
    Parse a connection URI into type and path.

    returns a tuple containing:
    - conn_name, conn_type, storage_unit, key_path

    The URI format is:
    <optional_conn_name>+<conn_type>://<storage_unit>/<key_path>
    where:
    - conn_name: optional name of the connection
    - conn_type: type of the connection (e.g., s3, az, gcs, http, https)
    - storage_unit: the storage unit (e.g., bucket, container, domain)
    - key_path: the path to the resource within the storage unit
    The function returns a tuple containing:
    - conn_name: the name of the connection 
        -   if not provided, defaults to 'default' 
            or the conn_type if it's an HTTP type
    - conn_type: the type of the connection
    - storage_unit: the storage unit
    - key_path: the path to the resource within the storage unit
    """
    valid_http_types = ['http', 'https'] if allow_http else []
    valid_conn_types = ['s3', 'az'] + valid_http_types
    # valid_conn_types = ['s3', 'az', 'gcs'] + valid_http_types

    conn, _, fullpath = uri.partition("://")
    if not conn:
        raise ValueError(f"Invalid connection URI: {uri}")
    
    conn_name, _, conn_type = conn.partition("+")
    if not conn_type:
        conn_type = conn_name
        conn_name = 'default' if conn_type not in valid_http_types else conn_name
    else:
        if conn_name != conn_type and conn_type in valid_http_types:
            raise ValueError(
                f"Invalid connection URI: {uri}. "
                f"Connection name '{conn_name}' cannot be used with HTTP types."
                f"Set connection name to '{conn_type}' for HTTP types."
            )

    if conn_type not in valid_conn_types:
        raise ValueError(
            f"Unsupported connection type: {conn_type}. "
            f"Supported types are: {valid_conn_types}"
        )

    if not fullpath:
        raise ValueError(f"Invalid connection URI: {uri}")
    
    storage_unit, _, key_path = fullpath.partition("/")
    if not storage_unit or not key_path:
        raise ValueError(f"Invalid connection URI: {uri}")
    
    return conn_name, conn_type, storage_unit, key_path


def str_to_bool(
        val: str
    ) -> bool:
    """
    Convert a string to a boolean value.
    """
    return str(val).strip().lower() in ("true", "1", "yes")



def false_or_path(
        val: str
    ) -> bool | str:
    """
    Convert a value to False if it is empty or None, otherwise return the value as a string.
    """
    if val in (None, "", "None", "False", "false", "0"):
        return False
    return str(val).strip()



def read_file(
        path: str
    ) -> Optional[str]:
    if path and os.path.isfile(path):
        with open(path, "r") as f:
            return f.read().strip()
    return None



def get_file_or_env(
        env_key: str, 
        fallback=None
    ) -> Optional[str]:
    """
    Return the value of ENV_VAR if set, otherwise try ENV_VAR_FILE
    as a path to read from. If neither is set, return fallback.
    """
    try:
        file_path = os.getenv(f"{env_key}_FILE")
        if file_path:
            val = read_file(file_path)
            if val is not None:
                return val
        return os.getenv(env_key, fallback)
    except Exception as e:
        print(f"Error loading value for {env_key}: {e}")
        return fallback


# Periodic cleanup of temporary files
# This function will run in a separate thread to clean up temporary files
# as fallback for the main task cleanup
def cleanup_tmp(
    chunk_cleanup_timeout: int
):
    while True:
        now = time.time()
        for f in Path("/tmp").iterdir():
            try:
                if f.is_file() and (now - f.stat().st_mtime) > chunk_cleanup_timeout:
                    f.unlink()
            except:
                pass
        time.sleep(60)


