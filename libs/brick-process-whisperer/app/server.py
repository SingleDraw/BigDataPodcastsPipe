import uvicorn
from app.submit import app  # FastAPI app

def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)
