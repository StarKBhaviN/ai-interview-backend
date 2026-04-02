from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time
import os
import tempfile
import json
import threading

# --- ROUTES ---
from routes import resume, admin, client, auth

# --- AI MODELS ---
from ai_models.stt import get_stt_transcriber
from ai_models.anti_cheat import get_anti_cheat_monitor
from ai_models.relevance_scorer import get_relevance_scorer
from ai_models.confidence_analyzer import get_confidence_analyzer

# --- SERVICES ---
from services.nlp import (
    extract_keywords,
    calculate_relevance,
    calculate_confidence,
    match_skills,
    is_technical_question
)
from services.evaluation import engine as evaluation_engine
from services.question_generator import generator as question_generator
from services.reporter import reporter

# --- INITIALIZATION ---
app = FastAPI(title="AI Interview Engine - v2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AI Singletons
transcriber = get_stt_transcriber()
anti_cheat = get_anti_cheat_monitor()

class AnalysisResponse(BaseModel):
    transcript: str
    relevance_score: float
    confidence_score: float
    sentiment: str
    keywords_found: list[str]
    is_technical: bool
    final_score: float

@app.get("/")
async def root():
    return {
        "status": "AI Engine Online", 
        "architecture": "v2.0",
        "models": ["STT-Whisper", "NLP-RoBERTa", "Audio-Librosa", "Vision-MediaPipe"]
    }

@app.post("/analyze-audio", response_model=AnalysisResponse)
async def analyze_audio(file: UploadFile = File(...), question: str = Form(None), skills: str = Form(None)):
    contents = await file.read()

    # 1. STT: Audio -> Text (Using central transcriber)
    transcript = transcriber.transcribe(contents)

    # 2. Confidence & Sentiment (Acoustic Prosody)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        conf_score, sentiment = calculate_confidence(transcript, tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    # 3. Relevance & NLP (RoBERTa + Heuristics)
    relevance = calculate_relevance(question, transcript) if question else 0.0
    keywords = extract_keywords(transcript)
    
    # Skills Processing
    resume_skills = [s.strip().lower() for s in skills.split(',')] if skills else []
    matched_skills = match_skills(transcript, resume_skills)
    all_keywords = list(set(keywords + matched_skills))
    
    is_tech = is_technical_question(question) if question else False

    # 4. Final Weighted Evaluation
    final_score = evaluation_engine.calculate_final_score(
        relevance=relevance,
        confidence=conf_score,
        sentiment=sentiment,
        matched_skills=matched_skills,
        total_skills=resume_skills
    )

    return AnalysisResponse(
        transcript=transcript,
        relevance_score=relevance,
        confidence_score=conf_score,
        sentiment=sentiment,
        keywords_found=all_keywords,
        is_technical=is_tech,
        final_score=final_score
    )

@app.post("/check-cheating")
async def check_cheating(
    frame: UploadFile = File(...),
    tab_switched: bool = Form(False),
    mic_muted: bool = Form(False)
):
    frame_bytes = await frame.read()
    
    # Vision-based check (Gaze + Person Count)
    result = anti_cheat.analyze_frame(frame_bytes)
    
    # Combined logic with browser signals
    if tab_switched:
        result["flags"].append("Tab switching detected")
        result["cheat_detected"] = True
    if mic_muted:
        result["flags"].append("Microphone muted")
        result["cheat_detected"] = True
        
    return result

@app.get("/api/ai/status")
async def get_ai_status():
    import json
    base_path = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_path, "ai_models/relevance_scorer/data/training_data.json")
    checkpoint_path = os.path.join(base_path, "ai_models/relevance_scorer/checkpoints/relevance_model")
    
    training_count = 0
    if os.path.exists(data_path):
        with open(data_path, "r") as f:
            training_count = len(json.load(f))
            
    is_trained = os.path.exists(checkpoint_path)
    
    return {
        "relevance": {
            "status": "Fine-tuned" if is_trained else "Base Model",
            "data_count": training_count,
            "can_train": training_count >= 5
        },
        "confidence": {
            "status": "Rule-based (V1)",
            "features": ["Pitch", "Energy", "Silence"]
        },
        "anti_cheat": {
            "status": "MediaPipe Mesh Active",
            "features": ["Gaze Tracking", "Multi-Face"]
        }
    }

@app.post("/api/ai/train-relevance")
async def train_relevance():
    from ai_models.relevance_scorer.train import fine_tune
    thread = threading.Thread(target=fine_tune)
    thread.start()
    return {"status": "Training started in background."}

@app.post("/api/generate-questions")
async def generate_questions(data: dict):
    skills = data.get("skills", ["general"])
    position = data.get("position", "Candidate")
    session = question_generator.generate_session(skills, position)
    return session

@app.post("/generate-report")
async def generate_report(data: dict):
    results = data.get("results", [])
    warnings = data.get("warnings", [])
    report = reporter.generate_report(results, warnings)
    return report

app.include_router(resume.router, prefix="/api")
app.include_router(admin.router)
app.include_router(client.router)
app.include_router(auth.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
