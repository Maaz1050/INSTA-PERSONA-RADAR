import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from dotenv import load_dotenv
import uvicorn

# We will import the engines here as we build them
# from src.fetcher import InstagramIngestor  

load_dotenv()

app = FastAPI(title="Insta Persona Radar")

# This is the secret key you will append to your cron-job.org URL
CRON_SECRET = os.getenv("CRON_SECRET_KEY")

def run_intelligence_pipeline():
    """Background task that runs the Ingestion and Intelligence planes."""
    print("[*] Pipeline triggered. Checking watchlist.txt...")
    
    # Placeholder for the architectural flow:
    # 1. Compare watchlist.txt against state/history.json
    # 2. Run fetcher.py for newly added users
    # 3. Pass data through Math, Vision, Text, and Synthesis engines
    # 4. Dispatch SMTP email via mailer.py
    
    print("[+] Pipeline execution finished.")

@app.get("/")
def health_check():
    """Default route to verify the server is alive on Render."""
    return {"status": "online", "service": "Persona Radar Webhook"}

@app.post("/trigger-radar")
def trigger_pipeline(secret: str, background_tasks: BackgroundTasks):
    """The secure endpoint hit by cron-job.org."""
    if not CRON_SECRET:
        raise HTTPException(status_code=500, detail="CRON_SECRET_KEY not configured on server.")
    
    if secret != CRON_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized ping.")
    
    background_tasks.add_task(run_intelligence_pipeline)
    return {"status": "success", "message": "Intelligence pipeline started in background."}
    
if __name__ == "__main__":
    # Render assigns a dynamic PORT environment variable automatically
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
