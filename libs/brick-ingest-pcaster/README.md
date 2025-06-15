### PCASTER - Podcast daily rankings scraper ###

command rule:

if --az-storage-account flag is present azure client is used
    for connection string auth there must be AZURE_STORAGE_KEY env provided
    for DefaultCredential Managed Identity must be properly set

if --s3-access-key flag is present boto3 client is used
    env secret key is a must then
    for local dev also url and ssl settings to False

PCaster prioritizes az storage flag if both are provided

# build image:
> use development.sh script in repo root


# check image size [1.5G]


# Example Commands:
> docker run pcaster:1.0.0 scrape --help
> DefaultCredentials:
docker run pcaster:1.0.0 pcaster --source apple_podcasts -p apple -c us --overwrite --azure-storage-account <storage_account_name>
> StringConnection:
docker run -e AZURE_STORAGE_KEY=<azure_storage_secret_key> pcaster:1.0.0 pcaster --source apple_podcasts -p apple -c us --overwrite --azure-storage-account <storage_account_name>


> SeaweedFS (local test s3):
docker run -e S3_SECRET_KEY=your_secret_key -e S3_ENDPOINT_URL=http://host.docker.internal:8333 -e S3_USE_SSL=False pcaster:1.0.1 pcaster --source apple_podcasts -p apple -c us --overwrite --s3-access-key your_access_key
