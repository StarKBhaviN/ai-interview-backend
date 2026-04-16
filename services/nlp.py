import re
from textblob import TextBlob
import numpy as np
import librosa
from ai_models.relevance_scorer import get_relevance_scorer
from ai_models.confidence_analyzer import get_confidence_analyzer

# Engines are now fetched lazily within functions to save memory.

# ------------------ KEYWORDS ------------------
def extract_keywords(text: str):
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())

    stopwords = set([
        "the","is","a","an","and","or","to","of","in","on","for","with",
        "this","that","it","as","are","was","were","be","by","from",
        "i","you","he","she","they","we","my","your"
    ])

    keywords = [w for w in words if w not in stopwords and len(w) > 3]

    return list(set(keywords))[:10]


# ------------------ SKILL MATCHING ------------------
def match_skills(transcript: str, skills: list[str]):
    if not skills:
        return []
        
    found = []
    text = transcript.lower()
    for skill in skills:
        if re.search(rf'\b{re.escape(skill.lower())}\b', text):
            found.append(skill)
            
    return found


# ------------------ SENTIMENT ------------------
def analyze_sentiment(text: str):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity

    if polarity > 0.2:
        return "Positive"
    elif polarity < -0.2:
        return "Negative"
    else:
        return "Neutral"


# ------------------ RELEVANCE ------------------
def calculate_relevance(question: str, answer: str):
    """
    Scores the relevance of a candidate's answer to the given question.
    Uses Model 2 (RoBERTa-base fine-tunable).
    """
    if not question:
        return 0.5

    if not answer or len(answer.strip().split()) < 3:
        return 0.05

    # Use the new fine-tunable inference engine
    relevance_engine = get_relevance_scorer()
    score = relevance_engine.score(question, answer)
    
    # 2. Length Bonus (Heuristic boost)
    word_count = len(answer.split())
    length_bonus = 0.0
    if word_count > 50:
        length_bonus = 0.1
    elif word_count > 20:
        length_bonus = 0.05

    final_score = score + length_bonus
    return round(min(1.0, max(0.0, final_score)), 2)


# ------------------ CONFIDENCE & SENTIMENT ------------------
def calculate_confidence(transcript: str, audio_path: str = None):
    """
    Analyzes confidence and sentiment from audio and transcript.
    Uses Model 3 (Confidence Analyzer V1).
    Returns: (confidence_score, sentiment_label)
    """
    # 0. Strict Content Check (Transcript)
    if not transcript or len(transcript.strip().split()) < 2:
        return 0.05, "Quiet/No Response"

    # 1. Audio-based (Acoustic Features via Model 3)
    audio_data = {"confidence_score": 0.7, "sentiment": "Neutral"}
    if audio_path:
        confidence_engine = get_confidence_analyzer()
        audio_data = confidence_engine.analyze(audio_path)

    # 2. Transcript-based (Filler words heuristic)
    words = transcript.lower().split()
    fillers = ["um", "uh", "like", "you know", "hmm"]
    filler_count = sum(words.count(f) for f in fillers)
    
    text_momentum = 1.0
    if len(words) > 0:
        # Penalize confidence if excessive fillers are used
        text_momentum = max(0.0, 1.0 - (filler_count / len(words)) * 4.0)

    # 3. Final Fusion
    # 60% Audio Prosody, 40% Text Momentum (Fillers)
    final_score = (audio_data["confidence_score"] * 0.6) + (text_momentum * 0.4)
    
    return round(float(final_score), 2), audio_data["sentiment"]


# ------------------ TECHNICAL DETECTION ------------------
def is_technical_question(question: str) -> bool:
    tech_keywords = [
        "coding", "react", "database", "python", "javascript", "java", "sql", 
        "backend", "frontend", "api", "hook", "component", "algorithm", "structure",
        "aws", "cloud", "docker", "git", "framework", "library", "technical", "stack"
    ]
    return any(kw in question.lower() for kw in tech_keywords)