# app/cli.py
import typer
import json
from pathlib import Path
from app.src.transcribe import transcribe
from typing import Optional

app = typer.Typer()

def load_batch_file(
        batch_path: Path
    ) -> list:
    """
    Batch path syntax:
    --batch default+s3://whisper/batch.json
    Load the batch file and return its content as a list of jobs. format:
    [
        {
            "input": "default+s3://bucket/podcast_1.mp3",
            "output": "s3://bucket/output1.txt"
        },
        {
            "input": "customblob+s3://bucket/podcast_2.mp3",
            "output": "default+az://container/output2.txt"
        }
    ]
    """
    from app.src.storages import storages   # Storage client provider
    from app.src.utils import parse_conn_uri
    # io for buffered reading
    from io import BytesIO

    # Get Source Client based on the batch_path parsed URI

    conn_name, conn_type, storage_unit, key_path = parse_conn_uri(batch_path)

    # prepare buffer for response
    batch_data = BytesIO()
    
    if conn_type in ["http", "https"]:
        # Use requests library to download the file for HTTP(S) sources
        import requests
        url = f"{conn_type}://{storage_unit}/{key_path}"
        response = requests.get(url, stream=True)
        # parse the JSON content
        
        if response.status_code == 200:
            batch_data.write(response.content)
            batch_data.seek(0)  # Important: rewind to beginning before reading
            jobs = json.load(batch_data)
            return jobs

    
    # Use the storage client to download the file
    storage = storages.get_client(
        name=conn_name,
        type=conn_type
    )

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< RENAME TO download_object after using violet-storage-lib
    storage.download_file(
        container_name=storage_unit,
        storage_key=key_path,
        # load the file into a buffer
        destination_path=batch_data 
    )

    batch_data.seek(0)  # Important: rewind to beginning before reading
    jobs = json.load(batch_data)
    return jobs



@app.command()
def submit(
    input: Optional[str] = typer.Option(None, help="Input file path"),
    output: Optional[str] = typer.Option(None, help="Output file path"),
    batch: Optional[str] = typer.Option(None, help="blob storage batch file path"),
    use_gpu: bool = typer.Option(False, help="Use GPU")
):
    if batch:
        # Load the batch file
        jobs = load_batch_file(batch)

        if not isinstance(jobs, list):
            typer.echo("Batch file must contain a list of jobs.")
            raise typer.Exit(code=1)

        for job in jobs:
            input = job.get("input")
            output = job.get("output")
            if not input or not output:
                typer.echo("Each job must have 'input' and 'output' fields.")
                continue

            typer.echo(f"Submitting: {input} → {output}")

            transcribe.delay(
                input = input,
                output = output,
                use_gpu = use_gpu
            ) 

        typer.echo("Batch submission completed.")

    elif input and output:
        # Single job submission
        typer.echo(f"Submitting: {input} → {output}")
        transcribe.delay(
            input, 
            output, 
            use_gpu
        )
        
    else:
        raise typer.BadParameter("Provide either --batch or --input and --output.")



if __name__ == "__main__":
    app()
