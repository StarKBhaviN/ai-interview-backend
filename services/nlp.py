import re
from textblob import TextBlob
from sentence_transformers import SentenceTransformer, util

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

    # 1. Semantic Similarity
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
def calculate_confidence(transcript: str):

    words = transcript.split()
    total_words = len(words)

    fillers = ["um", "uh", "like", "you know", "hmm"]
    filler_count = sum(transcript.lower().count(f) for f in fillers)

    if total_words == 0:
        return 0.0

    confidence = max(0, 1 - (filler_count / total_words))

    return round(confidence, 2)