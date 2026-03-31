from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time

from routes import resume
from services.speech_to_text import transcribe_audio
from services.nlp import (
    extract_keywords,
    analyze_sentiment,
    calculate_relevance,
    calculate_confidence,
    match_skills,
    is_technical_question
)


app = FastAPI(title="AI Interview Inference Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalysisResponse(BaseModel):
    transcript: str
    relevance_score: float
    confidence_score: float
    sentiment: str
    keywords_found: list[str]
    is_technical: bool

@app.get("/")
async def root():
    return {"status": "AI Engine Online", "models_loaded": ["Whisper-Base", "RoBERTa-Relevance", "Wav2Vec-Confidence"]}

@app.post("/analyze-audio", response_model=AnalysisResponse)
async def analyze_audio(file: UploadFile = File(...), question: str = Form(None), skills: str = Form(None)):
    contents = await file.read()

    # ✅ Step 1: Speech → Text
    transcript = transcribe_audio(contents)

    # ✅ Step 2: NLP & Audio Processing
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        confidence = calculate_confidence(transcript, tmp_path)
    finally:
        os.remove(tmp_path)

    keywords = extract_keywords(transcript)
    sentiment = analyze_sentiment(transcript)

    # Process skills from frontend
    resume_skills = [s.strip().lower() for s in skills.split(',')] if skills else []
    if not resume_skills:
        resume_skills = ["react", "node", "python", "mongodb"]

    relevance = calculate_relevance(question, transcript) if question else 0.0
    
    # Identify which resume skills were mentioned
    matched_skills = match_skills(transcript, resume_skills)
    
    # Combine keywords with matched skills for a better response
    all_keywords = list(set(keywords + matched_skills))

    # Identify if question is technical
    is_tech = is_technical_question(question) if question else False

    return AnalysisResponse(
        transcript=transcript,
        relevance_score=relevance,
        confidence_score=confidence,
        sentiment=sentiment,
        keywords_found=all_keywords,
        is_technical=is_tech
    )



from services.proctoring import engine as proctoring_engine

@app.post("/check-cheating")
async def check_cheating(
    frame: UploadFile = File(...),
    tab_switched: bool = Form(False),
    mic_muted: bool = Form(False)
):
    contents = await frame.read()
    result = await proctoring_engine.analyze_frame(contents)
    
    # Add frontend-detected flags to the result
    if tab_switched:
        result["flags"].append("Tab switching detected")
        result["cheat_detected"] = True
    if mic_muted:
        result["flags"].append("Microphone muted")
        result["cheat_detected"] = True
        
    return result

app.include_router(resume.router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
