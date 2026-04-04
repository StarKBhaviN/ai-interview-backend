from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List
import os
import json
from datetime import datetime

router = APIRouter(prefix="/api/client")

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
MEETINGS_DIR = os.path.join(DATA_DIR, "meetings")
SESSIONS_DIR = os.path.join(DATA_DIR, "sessions")

# Ensure directories exist
os.makedirs(MEETINGS_DIR, exist_ok=True)
os.makedirs(SESSIONS_DIR, exist_ok=True)

class QuestionItem(BaseModel):
    text: str
    difficulty: str = "Medium"
    category: str = "General"

class Meeting(BaseModel):
    id: str
    title: str
    code: str
    date: str
    time: str
    clientId: str
    company: str
    jobType: str = "Full-time"  # Full-time, Part-time, Internship
    location: str = "Remote"    # Remote, On-site, Hybrid
    department: str = "General"
    requirements: Optional[str] = ""
    status: str = "Open"
    candidates: int = 0
    questions: Optional[List[QuestionItem]] = []

class StatusUpdate(BaseModel):
    status: str

@router.get("/meetings")
async def list_meetings(client_id: str = None):
    meetings = []
    for filename in os.listdir(MEETINGS_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(MEETINGS_DIR, filename), "r") as f:
                meeting_data = json.load(f)
                
                # Filter by clientId if provided (Employer View)
                if client_id and meeting_data.get("clientId") != client_id:
                    continue
                    
                # If candidate view (no client_id), only show Open meetings
                if not client_id and meeting_data.get("status") != "Open":
                    continue
                    
                # Count candidates for this meeting
                meeting_code = meeting_data.get("code")
                candidate_count = 0
                for session_file in os.listdir(SESSIONS_DIR):
                    if session_file.endswith(".json"):
                        with open(os.path.join(SESSIONS_DIR, session_file), "r") as sf:
                            session_data = json.load(sf)
                            if session_data.get("meetingCode") == meeting_code:
                                candidate_count += 1
                meeting_data["candidates"] = candidate_count
                meetings.append(meeting_data)
    
    # Sort by date descending
    meetings.sort(key=lambda x: x.get("date", ""), reverse=True)
    return meetings

@router.post("/meetings")
async def create_meeting(meeting: Meeting):
    file_path = os.path.join(MEETINGS_DIR, f"{meeting.id}.json")
    with open(file_path, "w") as f:
        json.dump(meeting.dict(), f, indent=2)
    return {"status": "success", "meeting": meeting}

@router.get("/meetings/by-code/{code}/questions")
async def get_meeting_questions(code: str):
    for filename in os.listdir(MEETINGS_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(MEETINGS_DIR, filename), "r") as f:
                m = json.load(f)
                if m.get("code") == code:
                    if m.get("status") == "Closed":
                        raise HTTPException(status_code=403, detail="This interview session is now closed.")
                    return {"questions": m.get("questions", []), "title": m.get("title"), "company": m.get("company")}
    raise HTTPException(status_code=404, detail="Meeting not found")

@router.get("/stats")
async def get_client_stats(client_id: str = None):
    # Filter meetings by clientId
    meetings = []
    allowed_codes = []
    for filename in os.listdir(MEETINGS_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(MEETINGS_DIR, filename), "r") as f:
                m = json.load(f)
                if not client_id or m.get("clientId") == client_id:
                    meetings.append(m)
                    allowed_codes.append(m["code"])

    sessions = []
    for filename in os.listdir(SESSIONS_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(SESSIONS_DIR, filename), "r") as f:
                s = json.load(f)
                # Only include sessions for this client's meetings
                if s.get("meetingCode") in allowed_codes:
                    sessions.append(s)
    
    total_candidates = len(sessions)
    pending_reviews = len([s for s in sessions if s.get("score", 0) < 60])
    hiring_rate = len([s for s in sessions if s.get("score", 0) >= 80]) / total_candidates * 100 if total_candidates > 0 else 0

    return {
        "activeInterviews": len(meetings),
        "totalCandidates": total_candidates,
        "pendingReviews": pending_reviews,
        "hiringRate": f"{round(hiring_rate)}%"
    }

@router.get("/candidates")
async def get_client_candidates(client_id: str = None):
    candidates = []
    
    # Map meeting codes to titles (filtered by clientId)
    meeting_map = {}
    allowed_codes = []
    for filename in os.listdir(MEETINGS_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(MEETINGS_DIR, filename), "r") as f:
                m = json.load(f)
                if not client_id or m.get("clientId") == client_id:
                    meeting_map[m["code"]] = m["title"]
                    allowed_codes.append(m["code"])

    for filename in os.listdir(SESSIONS_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(SESSIONS_DIR, filename), "r") as f:
                s = json.load(f)
                if s.get("meetingCode") in allowed_codes:
                    candidates.append({
                        "id": s.get("id"),
                        "name": s.get("position") + " Candidate",
                        "email": s.get("email", "N/A"),
                        "meetingCode": s.get("meetingCode"),
                        "interviewName": meeting_map.get(s.get("meetingCode"), s.get("position")),
                        "score": s.get("score", 0),
                        "status": "Completed",
                        "date": s.get("date", "")
                    })
    
    # Sort by score High -> Low
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates

@router.delete("/meetings/{meeting_id}")
async def delete_meeting(meeting_id: str):
    file_path = os.path.join(MEETINGS_DIR, f"{meeting_id}.json")
    if os.path.exists(file_path):
        os.remove(file_path)
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Meeting not found")

@router.patch("/meetings/{meeting_id}")
async def update_meeting_status(meeting_id: str, update: StatusUpdate):
    file_path = os.path.join(MEETINGS_DIR, f"{meeting_id}.json")
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            meeting_data = json.load(f)
        meeting_data["status"] = update.status
        with open(file_path, "w") as f:
            json.dump(meeting_data, f, indent=2)
        return {"status": "success", "meeting": meeting_data}
    raise HTTPException(status_code=404, detail="Meeting not found")
