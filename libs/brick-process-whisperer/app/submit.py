import asyncio
from fastapi import FastAPI, Query, WebSocket
from app.src import transcribe
from app.src.broker import broker as r  # Redis client for tracking progress

# --- FastAPI app ---

app = FastAPI()

@app.post("/submit")
async def submit_transcription(
    input: str = Query(..., description="Input S3 URI"),
    output: str = Query(..., description="Output S3 URI"),
    use_gpu: bool = Query(False, description="Use GPU for transcription")
):
    """
    Submit a transcription job to the Celery worker.
    """
    # Call the transcribe function with the provided parameters
    result = transcribe.delay(
        input,
        output,
        use_gpu=use_gpu
    )
    return {"task_id": result.id, "message": "Job submitted"}


@app.websocket("/ws/{task_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    task_id: str
):
    """
    WebSocket endpoint to track the progress of a transcription job.
    """
    await websocket.accept()
    last_value = ""
    
    while True:
        progress = r.get(f"task_progress:{task_id}")
        if progress and progress != last_value:
            await websocket.send_text(progress)
            last_value = progress

        if progress == "Completed":
            break

        await asyncio.sleep(1)
    await websocket.close()
