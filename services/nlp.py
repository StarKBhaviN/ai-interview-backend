import re
from textblob import TextBlob
from sentence_transformers import SentenceTransformer, util
import librosa
import numpy as np

model = SentenceTransformer('all-MiniLM-L6-v2')

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
        # Simple string match for each skill
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
    if not question:
        return 0.5  # Neutral fallback

    # 1. Strict Content Check
    if not answer or len(answer.strip().split()) < 3:
        return 0.05 # Near zero for non-responses

    # 2. Semantic Similarity
    emb1 = model.encode(question, convert_to_tensor=True)
    emb2 = model.encode(answer, convert_to_tensor=True)
    similarity = util.pytorch_cos_sim(emb1, emb2).item()
    
    # 2. Length Bonus
    # If the question is "Tell us about yourself" and they speak a lot, it's relevant.
    word_count = len(answer.split())
    length_bonus = 0.0
    if word_count > 50:
        length_bonus = 0.2
    elif word_count > 20:
        length_bonus = 0.1

    # 3. Generic Question Leniency
    generic_keywords = ["background", "yourself", "intro", "experience", "tell", "about"]
    is_generic = any(kw in question.lower() for kw in generic_keywords)
    
    final_score = similarity + length_bonus
    if is_generic:
        final_score += 0.15 # Give boost to intros if they spoke enough

    # Normalize to 0–1
    return round(min(1.0, max(0, final_score)), 2)


# ------------------ TECHNICAL DETECTION ------------------
def is_technical_question(question: str) -> bool:
    tech_keywords = [
        "coding", "react", "database", "python", "javascript", "java", "sql", 
        "backend", "frontend", "api", "hook", "component", "algorithm", "structure",
        "aws", "cloud", "docker", "git", "framework", "library", "technical", "stack"
    ]
    return any(kw in question.lower() for kw in tech_keywords)


# ------------------ CONFIDENCE ------------------
def calculate_confidence(transcript: str, audio_path: str = None):
    # 0. Strict Content Check
    if not transcript or len(transcript.strip().split()) < 2:
        return 0.05 # Near zero for no speech

    # 1. Transcript-based (Filler words)
    words = transcript.split()
    total_words = len(words)
    fillers = ["um", "uh", "like", "you know", "hmm"]
    filler_count = sum(transcript.lower().count(f) for f in fillers)
    
    text_confidence = 1.0
    if total_words > 0:
        text_confidence = max(0, 1 - (filler_count / total_words) * 3) # Penalty multiplier

    # 2. Audio-based (Voice features)
    audio_confidence = 0.8 # Fallback
    
    if audio_path:
        try:
            # Load with very short duration to keep it fast
            y, sr = librosa.load(audio_path, duration=30)
            
            # RMS Energy (Volume)
            rms = librosa.feature.rms(y=y)[0]
            avg_rms = np.mean(rms)
            # Normalize RMS: 0.01 is very quiet, 0.05 is good energy
            energy_score = min(1.0, avg_rms / 0.04) 

            # Silent Intervals (Hesitation)
            non_silent = librosa.effects.split(y, top_db=25)
            total_duration = len(y) / sr
            if total_duration > 0:
                speech_duration = sum([(end - start) for start, end in non_silent]) / sr
                silence_ratio = (total_duration - speech_duration) / total_duration
                # High silence ratio = low confidence
                hesitation_score = max(0, 1 - silence_ratio * 1.5)
            else:
                hesitation_score = 0.1
                energy_score = 0.1 # Very quiet

            # Speech Rate (Estimating syllables)
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
            rate_score = min(1.0, tempo / 120) if isinstance(tempo, (float, int)) else 0.8

            if energy_score < 0.15:
                # Override: If volume is very low, it's not a confident answer
                audio_confidence = energy_score
            else:
                audio_confidence = (energy_score * 0.4) + (hesitation_score * 0.4) + (rate_score * 0.2)
            
        except Exception as e:
            print(f"Audio analysis error: {e}")
            audio_confidence = 0.7

    # Weighted Average: 70% Voice, 30% Text Clarity
    final_confidence = (audio_confidence * 0.7) + (text_confidence * 0.3)
    return round(float(final_confidence), 2)