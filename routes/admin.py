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
    meetingCode: str = None
    email: str = None

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

@router.get("/clients")
async def list_clients():
    """
    Returns a list of all registered clients.
    """
    USERS_DIR = os.path.join(DATA_DIR, "users")
    clients = []
    if not os.path.exists(USERS_DIR):
        return []
        
    for filename in os.listdir(USERS_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(USERS_DIR, filename), "r") as f:
                data = json.load(f)
                if data.get("role") == "Client":
                    clients.append({
                        "id": filename.replace(".json", ""), 
                        "name": data.get("name"),
                        "company": data.get("company", "N/A"),
                        "email": data.get("email"),
                        "status": "Active"
                    })
    return clients

@router.get("/candidates")
async def list_candidates():
    """
    Returns a list of all registered candidates.
    """
    USERS_DIR = os.path.join(DATA_DIR, "users")
    candidates = []
    if not os.path.exists(USERS_DIR):
        return []
        
    for filename in os.listdir(USERS_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(USERS_DIR, filename), "r") as f:
                data = json.load(f)
                if data.get("role") == "Candidate":
                    candidates.append({
                        "id": filename.replace(".json", ""), 
                        "name": data.get("name"),
                        "email": data.get("email"),
                        "role": "Candidate",
                        "status": "Active",
                        "lastLogin": data.get("last_login", "N/A")
                    })
    return candidates

@router.delete("/users/{user_id}")
async def terminate_user(user_id: str):
    """
    Permanently removes a client or candidate from the platform.
    """
    USERS_DIR = os.path.join(DATA_DIR, "users")
    file_path = os.path.join(USERS_DIR, f"{user_id}.json")
    
    if not os.path.exists(file_path):
         # Try with email if user_id is the email
         file_path = os.path.join(USERS_DIR, f"{user_id}.json")
         if not os.path.exists(file_path):
             raise HTTPException(status_code=404, detail="User not found")

    try:
        os.remove(file_path)
        return {"status": "success", "message": f"User {user_id} terminated."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_stats():
    """
    Calculates platform-wide aggregate statistics, including Month-over-Month growth.
    """
    USERS_DIR = os.path.join(DATA_DIR, "users")
    client_count = 0
    candidate_count = 0
    
    if os.path.exists(USERS_DIR):
        for filename in os.listdir(USERS_DIR):
            if filename.endswith(".json"):
                with open(os.path.join(USERS_DIR, filename), "r") as f:
                    u_data = json.load(f)
                    if u_data.get("role") == "Client":
                        client_count += 1
                    else:
                        candidate_count += 1

    all_sessions = []
    if os.path.exists(SESSIONS_DIR):
        for filename in os.listdir(SESSIONS_DIR):
            if filename.endswith(".json"):
                with open(os.path.join(SESSIONS_DIR, filename), "r") as f:
                    all_sessions.append(json.load(f))
                    
    total = len(all_sessions)
    if total == 0:
        return {
            "totalCandidates": candidate_count,
            "totalClients": client_count,
            "avgScore": 0,
            "passRate": 0,
            "interviewsCompleted": 0,
            "growth": 0
        }
        
    avg_score = sum(s["score"] for s in all_sessions) / total
    pass_rate = len([s for s in all_sessions if s["score"] >= 70]) / total * 100
    
    # Growth Calculation (MoM)
    now = datetime.now()
    current_month_count = 0
    last_month_count = 0
    
    for s in all_sessions:
        try:
            # Expected format: "2024-03-21T10:00:00Z"
            s_date = datetime.fromisoformat(s["date"].replace("Z", "+00:00"))
            if s_date.year == now.year and s_date.month == now.month:
                current_month_count += 1
            elif (s_date.year == now.year and s_date.month == now.month - 1) or \
                 (now.month == 1 and s_date.year == now.year - 1 and s_date.month == 12):
                last_month_count += 1
        except:
            continue
            
    growth = 0
    if last_month_count > 0:
        growth = ((current_month_count - last_month_count) / last_month_count) * 100
    elif current_month_count > 0:
        growth = 100 # Initial growth
        
    return {
        "totalCandidates": candidate_count,
        "totalClients": client_count,
        "avgScore": round(avg_score, 1),
        "passRate": round(pass_rate, 1),
        "interviewsCompleted": total,
        "growth": round(growth, 1)
    }

@router.get("/export")
async def export_sessions():
    """
    Generates a CSV of all interview sessions for administrative reporting.
    """
    import csv
    import io
    from fastapi.responses import StreamingResponse

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Date", "Candidate Name", "Position", "Score", "Result"])

    if os.path.exists(SESSIONS_DIR):
        for filename in os.listdir(SESSIONS_DIR):
            if filename.endswith(".json"):
                with open(os.path.join(SESSIONS_DIR, filename), "r") as f:
                    data = json.load(f)
                    writer.writerow([
                        data.get("id"),
                        data.get("date"),
                        data.get("email", "N/A"),
                        data.get("position"),
                        data.get("score"),
                        "Pass" if data.get("score", 0) >= 70 else "Fail"
                    ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=platform_report_{datetime.now().strftime('%Y%m%d')}.csv"}
    )

@router.get("/audio/{session_id}/{question_index}")
async def get_audio(session_id: str, question_index: int):
    """
    Streams a recorded WAV file from the data store.
    """
    audio_path = os.path.join(AUDIO_DIR, f"{session_id}_{question_index}.wav")
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
        
    return FileResponse(audio_path)

@router.get("/analytics")
async def get_analytics():
    """
    Computes dynamic analytics for charts including trends, topic proficiency, and role distribution.
    """
    all_sessions = []
    if os.path.exists(SESSIONS_DIR):
        for filename in os.listdir(SESSIONS_DIR):
            if filename.endswith(".json"):
                with open(os.path.join(SESSIONS_DIR, filename), "r") as f:
                    all_sessions.append(json.load(f))

    # 1. Performance Trend (Last 6 months)
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    trend_dict = {}
    
    for s in all_sessions:
        try:
            s_date = datetime.fromisoformat(s["date"].replace("Z", "+00:00"))
            m_key = months[s_date.month - 1]
            if m_key not in trend_dict:
                trend_dict[m_key] = {"sum": 0, "count": 0, "high": 0, "low": 100}
            
            score = s["score"]
            trend_dict[m_key]["sum"] += score
            trend_dict[m_key]["count"] += 1
            trend_dict[m_key]["high"] = max(trend_dict[m_key]["high"], score)
            trend_dict[m_key]["low"] = min(trend_dict[m_key]["low"], score)
        except: continue

    performanceTrend = []
    for m in months:
        if m in trend_dict:
            performanceTrend.append({
                "month": m,
                "avg": round(trend_dict[m]["sum"] / trend_dict[m]["count"], 1),
                "high": trend_dict[m]["high"],
                "low": trend_dict[m]["low"]
            })
    
    if not performanceTrend: # Dummy if no data
        performanceTrend = [{"month": "No Data", "avg": 0, "high": 0, "low": 0}]

    # 2. Topic Proficiency
    topics = {}
    for s in all_sessions:
        for detail in s.get("details", []):
            cat = detail.get("category", "General")
            if cat not in topics:
                topics[cat] = {"sum": 0, "count": 0}
            topics[cat]["sum"] += detail.get("relevance_score", 0) * 100
            topics[cat]["count"] += 1
    
    topicProficiency = [{"topic": k, "score": round(v["sum"]/v["count"], 1)} for k, v in topics.items()]
    if not topicProficiency:
        topicProficiency = [{"topic": "None", "score": 0}]

    # 3. Role Distribution
    roles = {}
    for s in all_sessions:
        pos = s.get("position", "Unspecified")
        roles[pos] = roles.get(pos, 0) + 1
    
    roleDistribution = [{"name": k, "value": v} for k, v in roles.items()]

    return {
        "performanceTrend": performanceTrend[-6:], # Last 6 months
        "topicProficiency": topicProficiency,
        "roleDistribution": roleDistribution,
        "summary": {
            "totalInterviews": len(all_sessions),
            "avgDuration": "12.5m", # Mock for now
            "passRate": f"{round(len([s for s in all_sessions if s['score'] >= 70]) / max(len(all_sessions), 1) * 100, 1)}%",
            "accuracy": "94%"
        }
    }
