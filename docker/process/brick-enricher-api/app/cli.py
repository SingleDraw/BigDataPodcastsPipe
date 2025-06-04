import typer, os
from app.app import run_pcaster
from typing import List, Optional

if os.getenv("ENVIRONMENT") != "production":
    from app.src.storage.local_client import LocalStorageClient as StorageClient
    from pathlib import Path
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
else:
    from app.src.storage.client import AzureBlobStorageClient as StorageClient

def parse_comma_env(value: Optional[str]) -> Optional[List[str]]:
    return value.split(",") if value else None

sources_env = parse_comma_env(os.getenv("PCASTER_SOURCES", None))
platforms_env = parse_comma_env(os.getenv("PCASTER_PLATFORMS", None))
countries_env = parse_comma_env(os.getenv("PCASTER_COUNTRIES", None))

app = typer.Typer()


@app.command("scrape")
def scrape_cmd(
    azure_storage_account: str = typer.Option(
        os.getenv("AZURE_STORAGE_ACCOUNT", ""), 
        help="Azure Storage Account name"
    ),
    overwrite: bool = typer.Option(
        False, 
        help="Overwrite blobs if they already exist"
    ),
    sources: Optional[List[str]] = typer.Option(
        sources_env,
        "--source", "-s", 
        help="List of sources", 
        show_default=False
    ),
    platforms: Optional[List[str]] = typer.Option(
        platforms_env,
        "--platform", "-p", 
        help="List of platforms", 
        show_default=False
    ),
    countries: Optional[List[str]] = typer.Option(
        countries_env,
        "--country", "-c", 
        help="List of countries", 
        show_default=False
    ),
    delay: int = typer.Option(
        1, 
        help="Delay in seconds between retries for storage upload failures"
    ),
    retries: int = typer.Option(
        3, 
        help="Number of retries for storage upload failures"
    )
    
):
    try:
        run_pcaster(        
            overwrite=overwrite,
            storage_client_constructor=StorageClient,
            azure_storage_account=azure_storage_account,
            azure_storage_key=os.getenv("AZURE_STORAGE_KEY", ""),
            sources=sources,
            platforms=platforms,
            countries=countries,
            delay=delay,
            retries=retries
        )
    except Exception as e:
        typer.echo(f"An error occurred during the scraping process: {e}", err=True)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()





# ----------------

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

key_vault_url = "https://<your-keyvault-name>.vault.azure.net/"
credential = DefaultAzureCredential()  # Automatically uses Azure CLI creds locally
client = SecretClient(vault_url=key_vault_url, credential=credential)

secret = client.get_secret("PodcastingIndexApiKey").value
print(secret)
