### PCASTER - Podcast daily rankings scraper ###


# build image:
> docker build -t pcaster:1.0.0 -f Dockerfile ./


# check image size [1.5G]:
> docker image inspect pcaster:1.0.0 --format='{{.Size}}' | numfmt --to=iec 


# Example Commands:
> docker run pcaster:1.0.0 scrape --help
> docker run pcaster:1.0.0 pcaster --source apple_podcasts -p apple -c us --overwrite --azure-storage-account <storage_account_name>
> docker run -e AZURE_STORAGE_KEY=<azure_storage_secret_key> pcaster:1.0.0 pcaster --source apple_podcasts -p apple -c us --overwrite --azure-storage-account <storage_account_name>
