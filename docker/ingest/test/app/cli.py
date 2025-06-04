import typer, os, requests
from azure.storage.blob import BlobServiceClient
from azure.keyvault.secrets import SecretClient


def run_app():
    # Test request to a public API
    try:
        response = requests.get("https://api.github.com")
        if response.status_code == 200:
            print("API request successful.")
        else:
            print(f"API request failed with status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"An error occurred during the API request: {e}")
        raise

# Test Azure Key Vault access
def test_key_vault():
    from azure.identity import DefaultAzureCredential
    try:
        # Initialize SecretClient with DefaultAzureCredential
        key_vault_url = os.getenv("AZURE_KEY_VAULT_URL")
        credential = DefaultAzureCredential()
        secret_client = SecretClient(vault_url=key_vault_url, credential=credential)
        
        # Access a specific secret
        secret_name = "PodcastingIndexApiKey"
        secret_value = secret_client.get_secret(secret_name).value
        print(f"Secret '{secret_name}' retrieved successfully: {secret_value}")
    except Exception as e:
        print(f"An error occurred while accessing the Key Vault: {e}")
        raise


def test_blob_write():
    try:
        # Initialize BlobServiceClient with DefaultAzureCredential
        storage_account = os.getenv("AZURE_STORAGE_ACCOUNT")
        storage_secret = os.getenv("AZURE_STORAGE_KEY")
        connection_string = f"DefaultEndpointsProtocol=https;AccountName={storage_account};AccountKey={storage_secret};EndpointSuffix=core.windows.net"
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        # Access a specific container and blob
        container_name = "whisperer"
        blob_name = "test_blob_one.txt"
        container_client = blob_service_client.get_container_client(container_name)
        blob_client = container_client.get_blob_client(blob_name)
        # Write a test blob
        blob_client.upload_blob("This is a test blob content.", overwrite=True)
        print(f"Blob '{blob_name}' written successfully to container '{container_name}'.")
    except Exception as e:
        print(f"An error occurred while writing the blob: {e}")
        raise

def test_blob_write_two():
    from azure.identity import DefaultAzureCredential
    try:
        # Initialize BlobServiceClient with DefaultAzureCredential
        storage_account = os.getenv("AZURE_STORAGE_ACCOUNT")

        credential = DefaultAzureCredential()

        blob_service_client = BlobServiceClient(
            account_url=f"https://{storage_account}.blob.core.windows.net",
            credential=credential
        )
        # Access a specific container and blob
        container_name = "whisperer"
        blob_name = "test_blob_two.txt"
        container_client = blob_service_client.get_container_client(container_name)
        blob_client = container_client.get_blob_client(blob_name)
        # Write a test blob
        blob_client.upload_blob("This is a test blob content.", overwrite=True)
        print(f"Blob '{blob_name}' written successfully to container '{container_name}'.")
    except Exception as e:
        print(f"An error occurred while writing the blob: {e}")
        raise

app = typer.Typer()


@app.command("write-blob")
def test_fn():
    try:
        # run_app() # Works with public API - Passed !
        test_blob_write() # Works with Azure Storage Blob using connection string
        # test_blob_write_two() # Works with Azure Storage Blob using DefaultAzureCredential
        # test_key_vault() # Works with Key Vault
    except Exception as e:
        typer.echo(f"An error occurred during the test app process: {e}", err=True)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()

