import typer, os, requests
from azure.storage.blob import BlobServiceClient
from azure.keyvault.secrets import SecretClient

# Request to a public API to test connectivity
# This function is used to ensure that the application can make HTTP requests successfully.
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
# This function retrieves a secret from Azure Key Vault using the DefaultAzureCredential.
# It requires the AZURE_KEY_VAULT_URL environment variable to be set.
def test_key_vault(
    secret_name: str = "PodcastingIndexApiKey"
):
    from azure.identity import DefaultAzureCredential
    try:
        # Initialize SecretClient with DefaultAzureCredential
        key_vault_url = os.getenv("AZURE_KEY_VAULT_URL")
        credential = DefaultAzureCredential()
        secret_client = SecretClient(vault_url=key_vault_url, credential=credential)
        
        # Access a specific secret
        secret_value = secret_client.get_secret(secret_name).value
        print(f"Secret '{secret_name}' retrieved successfully: {secret_value}")
    except Exception as e:
        print(f"An error occurred while accessing the Key Vault: {e}")
        raise

# Test Azure Blob Storage write operation
# This function writes a test blob to Azure Blob Storage using the BlobServiceClient.
# It requires the AZURE_STORAGE_ACCOUNT and AZURE_STORAGE_KEY environment variables to be set.
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

# Test Azure Blob Storage write operation using DefaultAzureCredential
# This function writes a test blob to Azure Blob Storage using the DefaultAzureCredential.
# It requires the AZURE_STORAGE_ACCOUNT environment variable to be set.
def test_blob_write_two():
    from azure.identity import DefaultAzureCredential
    try:
        # Initialize BlobServiceClient with DefaultAzureCredential
        storage_account = os.getenv("AZURE_STORAGE_ACCOUNT")

        if not storage_account:
            raise ValueError("AZURE_STORAGE_ACCOUNT environment variable is not set.")

        credential = DefaultAzureCredential()

        if not credential:
            raise ValueError("DefaultAzureCredential could not be initialized.")

        blob_service_client = BlobServiceClient(
            account_url=f"https://{storage_account}.blob.core.windows.net",
            credential=credential
        )

        if not blob_service_client:
            raise ValueError("BlobServiceClient could not be initialized.")
        
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
def test_fn(
    write_blob: bool = typer.Option(False, "--write-blob", "-w", help="Write a test blob to Azure Storage Blob", show_default=False),
    write_blob_two: bool = typer.Option(False, "--write-blob-default", "-w2", help="Write a test blob to Azure Storage Blob using DefaultAzureCredential", show_default=False),
    key_vault: str = typer.Option(..., "--key-vault", "-k", help="Name of the secret in Azure Key Vault to retrieve", show_default=False, metavar="SECRET_NAME")
):
    try:
        run_app()                   # Works !
        if write_blob:
            test_blob_write()       # Works !
        if write_blob_two:
            test_blob_write_two()
        if key_vault:               # Works ! 
            test_key_vault(
                secret_name=key_vault
            )
    except Exception as e:
        typer.echo(f"Error during the test app: {e}", err=True)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()

