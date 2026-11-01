import os
import json
from fastapi import FastAPI, HTTPException, BackgroundTasks
from dotenv import load_dotenv
import uvicorn

# Import our custom architecture
from src.fetcher import InstagramIngestor
from src.engines.math_engine import MathEngine
from src.engines.vision_engine import VisionEngine
from src.engines.text_engine import TextEngine
from src.engines.synthesizer import SynthesizerEngine
from src.mailer import Mailer

load_dotenv()
app = FastAPI(title="Insta Persona Radar")
CRON_SECRET = os.getenv("CRON_SECRET_KEY")

def run_intelligence_pipeline():
    """The master function that orchestrates the entire pipeline."""
    print("[*] Pipeline triggered. Checking for new targets...")
    
    # 1. Load Watchlist & History
    with open("watchlist.txt", "r", encoding="utf-8") as f:
        watchlist = [line.strip().lstrip("@") for line in f if line.strip() and not line.startswith("#")]
        
    history_file = "state/history.json"
    os.makedirs("state", exist_ok=True)
    history = {}
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as f:
            history = json.load(f)

    # 2. Identify new users
    new_users = [user for user in watchlist if user not in history]
    if not new_users:
        print("[*] No new users to analyze. Pipeline resting.")
        return

    # 3. Initialize Engines
    ingestor = InstagramIngestor()
    math_engine = MathEngine()
    vision_engine = VisionEngine()
    text_engine = TextEngine()
    synth_engine = SynthesizerEngine()
    
    completed_reports = []

    # 4. Run the Pipeline for each new user
    for username in new_users:
        print(f"\n[*] Commencing extraction on @{username}...")
        
        raw_data = ingestor.fetch_profile(username)
        if not raw_data or not raw_data.get("posts"):
            history[username] = "Failed or Private"
            continue

        math_out = math_engine.analyze(raw_data)
        vision_out = vision_engine.analyze(raw_data)
        text_out = text_engine.analyze(raw_data)
        
        synth_out = synth_engine.analyze(raw_data, math_out, vision_out, text_out)

        completed_reports.append({
            "profile": raw_data.get("profile"),
            "math": math_out,
            "vision": vision_out,
            "text": text_out,
            "synth": synth_out
        })
        
        # Mark as successfully processed
        history[username] = "Analyzed"

    # 5. Delivery & State Update
    if completed_reports:
        mailer = Mailer()
        mailer.send_report(new_users, completed_reports)
        
        # Save updated history back to disk
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4)
            
    print("[+] Pipeline execution finished.")

@app.get("/")
def health_check():
    return {"status": "online", "service": "Persona Radar Webhook"}

@app.post("/trigger-radar")
def trigger_pipeline(secret: str, background_tasks: BackgroundTasks):
    if not CRON_SECRET:
        raise HTTPException(status_code=500, detail="CRON_SECRET_KEY missing.")
    if secret != CRON_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized.")
    
    background_tasks.add_task(run_intelligence_pipeline)
    return {"status": "success", "message": "Pipeline started in background."}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
