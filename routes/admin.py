from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import json
import shutil
from datetime import datetime

router = APIRouter(prefix="/api/admin")

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
SESSIONS_DIR = os.path.join(DATA_DIR, "sessions")
AUDIO_DIR = os.path.join(DATA_DIR, "audio")

# Ensure directories exist
os.makedirs(SESSIONS_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

class SessionUpdate(BaseModel):
    id: str
    date: str
    position: str
    score: float
    questionsCount: int
    warnings: list
    details: list
    report: dict

@router.post("/sessions/submit")
async def submit_session(session: SessionUpdate):
    """
    Saves a completed interview session to the JSON data store.
    """
    session_id = session.id
    file_path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    
    # Save the JSON data
    with open(file_path, "w") as f:
        json.dump(session.dict(), f, indent=2)
        
    return {"status": "success", "session_id": session_id}

@router.post("/audio/upload")
async def upload_audio(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    question_index: int = Form(...)
):
    """
    Uploads a recorded WAV file to the persistent store.
    """
    audio_path = os.path.join(AUDIO_DIR, f"{session_id}_{question_index}.wav")
    with open(audio_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"status": "success", "audio_path": audio_path}

@router.get("/sessions")
async def list_sessions():
    """
    Returns a list of all completed interview sessions.
    """
    sessions = []
    if not os.path.exists(SESSIONS_DIR):
        return []
        
    for filename in os.listdir(SESSIONS_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(SESSIONS_DIR, filename), "r") as f:
                data = json.load(f)
                # Return summary only for list
                sessions.append({
                    "id": data["id"],
                    "date": data["date"],
                    "position": data["position"],
                    "score": data["score"],
                    "status": "Completed"
                })
    
    # Sort by date descending
    sessions.sort(key=lambda x: x["date"], reverse=True)
    return sessions

@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """
    Retrieves the full detail of a specific interview session.
    """
    file_path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Session not found")
        
    with open(file_path, "r") as f:
        return json.load(f)

@router.get("/stats")
async def get_stats():
    """
    Calculates platform-wide aggregate statistics.
    """
    all_sessions = []
    if os.path.exists(SESSIONS_DIR):
        for filename in os.listdir(SESSIONS_DIR):
            if filename.endswith(".json"):
                with open(os.path.join(SESSIONS_DIR, filename), "r") as f:
                    all_sessions.append(json.load(f))
                    
    total = len(all_sessions)
    if total == 0:
        return {
            "totalCandidates": 0,
            "avgScore": 0,
            "passRate": 0,
            "interviewsCompleted": 0
        }
        
    avg_score = sum(s["score"] for s in all_sessions) / total
    pass_rate = len([s for s in all_sessions if s["score"] >= 70]) / total * 100
    
    return {
        "totalCandidates": total,
        "avgScore": round(avg_score, 1),
        "passRate": round(pass_rate, 1),
        "interviewsCompleted": total
    }

@router.get("/audio/{session_id}/{question_index}")
async def get_audio(session_id: str, question_index: int):
    """
    Streams a recorded WAV file from the data store.
    """
    # Note: In the current Tauri-based setup, audio is stored in temp paths on the client's FS.
    # To make this cross-platform/real, we would need to upload the WAVs during submission.
    # For now, this is a placeholder for the future centralized storage.
    audio_path = os.path.join(AUDIO_DIR, f"{session_id}_{question_index}.wav")
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
        
    return FileResponse(audio_path)
