from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="NEMESIS Studio Backend",
    description="REST API server for running and managing NEMESIS runs",
    version="0.1.0"
)

# Enable CORS for the Panel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "message": "NEMESIS Studio backend API is running.",
        "status": "ready"
    }

@app.get("/status")
def get_status():
    # Placeholder status endpoint
    return {
        "status": "idle",
        "current_run": None,
        "api_version": "0.1.0"
    }

if __name__ == "__main__":
    print("Starting NEMESIS Studio backend server...")
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
