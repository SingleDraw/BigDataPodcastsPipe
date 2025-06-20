# app/cli.py
import typer
from app.src import load_batch, transcribe
from typing import Optional

# -- Celery Submitter Cli --

app = typer.Typer()

@app.command()
def submit(
    input: Optional[str] = typer.Option(None, help="Input file path"),
    output: Optional[str] = typer.Option(None, help="Output file path"),
    batch: Optional[str] = typer.Option(None, help="blob storage batch file path"),
    use_gpu: bool = typer.Option(False, help="Use GPU")
):
    queue_name = "transcription_queue"  # Default queue name for transcription tasks

    # Load the batch file
    if batch:
        jobs = load_batch(batch_path=batch)

        if not isinstance(jobs, list):
            typer.echo("Batch file must contain a list of jobs.")
            raise typer.Exit(code=1)

        for job in jobs:
            input_file, output_file = job.get("input"), job.get("output")
            if not input_file or not output_file:
                typer.echo("Each job must have 'input' and 'output' fields.")
                continue
            typer.echo(f"Submitting: {input_file} → {output_file}")

            transcribe.apply_async(
                args=(input_file, output_file, use_gpu),
                queue=queue_name,
                routing_key='whisper_transcription'
            )

        typer.echo("Batch submission completed.")

    # Single job submission
    elif input and output:
        typer.echo(f"Submitting: {input} → {output}")

        transcribe.apply_async(
            args=(input, output, use_gpu),
            queue=queue_name,
            routing_key='whisper_transcription'
        )
        
    else:
        raise typer.BadParameter("Provide either --batch or --input and --output.")



if __name__ == "__main__":
    app()
