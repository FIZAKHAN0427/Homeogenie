# main.py
import os
import uvicorn
from .api import app

def run_app():
    uvicorn.run(
        app, 
        host=os.getenv("APP_HOST", "0.0.0.0"), 
        port=int(os.getenv("APP_PORT", 8000))
    )

if __name__ == "__main__":
    run_app()