
import os
import logging
from typing import List, Dict, Any
from storage_lib import StorageClient
from app.src.utils import str_to_bool, false_or_path, get_file_or_env
from app.conf.conf import (
    _default_storage_name,
    _blob_storage_type,
    _s3_storage_type
)

STORAGE_CONFIGURATIONS_DIR = 'config/'

class Storages:
    """
    Singleton class to manage storage configurations.
    """
    _instance = None

    def __new__(
            cls
        ):
        if cls._instance is None:
            cls._instance = super(Storages, cls).__new__(cls)
            cls._instance.storages = []
        return cls._instance



    def __init__(
            self
        ):
        self.configs = self.read_storage_configs()
        self.read_env_config()



    def get_client(
            self, 
            name: str = _default_storage_name,
            type: str = None
        ) -> object:
        """
        Returns the storage client by name.
        """
        for config in self.configs:
            if config.get("conn.name", None) == name:
                if type and config.get("conn.type") != type:
                    continue
                print(f"Found config: {name} of type {config.get('conn.type')}")
                return self.get_storage_client(config)
        raise ValueError(f"Storage client with name '{name}' not found.")
    

    
    def read_env_config(
            self
        ) -> Dict[str, Any]:
        """
        Reads the environment configuration and populates the configs list.
        NOTE: Be Cautious! Config read from environment variables will override 
        configs read from files with the same name.
        """
        env_config = None
        if (
            os.getenv("AWS_ACCESS_KEY_ID")
            or os.getenv("AWS_ACCESS_KEY_ID_FILE")
        ):                   
            # Amazon S3 or compatible storage
            env_config = {
                "conn.name": _default_storage_name,
                "conn.type": _s3_storage_type,
                "conn.aws_access_key_id": get_file_or_env("AWS_ACCESS_KEY_ID"),
                "conn.aws_secret_access_key": get_file_or_env("AWS_SECRET_ACCESS_KEY"),
                "conn.endpoint_url": os.getenv("S3_ENDPOINT_URL", None),
                "conn.use_ssl": str_to_bool(os.getenv("S3_USE_SSL", "false")),
                # "conn.verify": false_or_path(os.getenv("S3_VERIFY_SSL", "false").lower()),
                "conn.region_name": os.getenv("AWS_REGION", None)
            }

        elif (
            os.getenv("AZURE_STORAGE_CONNECTION_STRING") 
            or os.getenv("AZURE_STORAGE_CONNECTION_STRING_FILE") 
            or os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
        ):  
            # Azure Blob Storage or emulator
            env_config = {
                "conn.name": _default_storage_name,
                "conn.type": _blob_storage_type,
                "conn.ConnectionString": get_file_or_env("AZURE_STORAGE_CONNECTION_STRING"),
                "conn.AccountName": os.getenv("AZURE_STORAGE_ACCOUNT_NAME", None),
                "conn.AccountKey": get_file_or_env("AZURE_STORAGE_ACCOUNT_KEY"),
            }

        # add config to configs
        if env_config is not None:
            # check if config already exists
            for existing_config in self.configs:
                if existing_config.get("conn.name") == env_config.get("conn.name"):
                    # replace existing config
                    existing_config.clear()
                    existing_config.update(env_config)
                    break
            self.configs.append(env_config)



    def read_storage_configs(
            self,
            storage_dir: str = STORAGE_CONFIGURATIONS_DIR
        ) -> List[str]:
        """
        Reads all files from the specified directory 
        and returns their contents as a dicts.
        Each file should contain key-value pairs in the format: key=value.
        Lines starting with '#' or empty lines are ignored.
        """

        configs = []

        try:
            for filename in os.listdir(storage_dir):
                if filename.endswith(".properties"):
                    with open(os.path.join(storage_dir, filename), 'r') as file:
                        config = {}

                        for line in file:
                            if line.startswith("#") or not line.strip():
                                continue

                            # split on first '='
                            key, value = line.strip().split('=', 1) 
                            config[key] = value

                        configs.append(config)

        except Exception as e:
            logging.error(f"Error reading storage configs: {e}")
        return configs
    

    
    def get_storage_client(
            self,
            config: dict,
            supported_conn_types: list = ["s3", "az"]
        ) -> object:
        """
        Returns the storage client 
        based on the connection type specified in the config.
        """

        conn_type = config.get("conn.type", None)

        if conn_type is None:
            raise ValueError("Misconfigured connection type.")
        
        if conn_type not in supported_conn_types:
            raise ValueError(
                f"Unsupported connection type: {conn_type}. "
                f"Supported types are: {supported_conn_types}"
            )
        
        if conn_type == _s3_storage_type:
            # Amazon S3 or compatible storage
            print(f"Creating S3 client for {config.get('conn.name', 'default')}")
            credentials = {
                "s3_access_key": config.get("conn.aws_access_key_id", None),
                "s3_secret_key": config.get("conn.aws_secret_access_key", None),
                "s3_endpoint_url": config.get("conn.endpoint_url", None),
                "s3_use_ssl": str_to_bool(config.get("conn.use_ssl", "true")),
                "s3_region_name": config.get("conn.region_name", None)
            }
        
        elif conn_type == _blob_storage_type:
            # Azure Blob Storage
            print(f"Creating Azure Blob Storage client for {config.get('conn.name', 'default')}")
            credentials = {
                "azure_storage_account": config.get("conn.AccountName", None),
                "azure_storage_key": config.get("conn.AccountKey", None),
                "azure_storage_connection_string": config.get("conn.ConnectionString", None)
            }

        else:
            raise ValueError(f"Unsupported connection type: {conn_type}. Supported types are: {supported_conn_types}")
        
        # Create and return the storage client
        return StorageClient( credentials=credentials )



storages = Storages()