import spacy
import json
import os
import re

_nlp = None

def get_spacy_model():
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except Exception as e:
            print(f"[skill_extractor.py] Error loading spacy model: {e}")
            _nlp = None
    return _nlp

def load_skills_db():
    """Reads the skills library from the local JSON file."""
    path = os.path.join(os.path.dirname(__file__), "skills_db.json")
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"[skill_extractor.py] Error loading skills_db.json: {e}")
        return {"technical": [], "soft": []}

def extract_skills(text: str) -> dict:
    """
    Main NLP function to extract structured data from resume text.
    Returns:
    {
        "technical": ["React", "Python", ...],
        "soft": ["Communication", ...],
        "entities": {"ORG": [...], "DATE": [...], ...},
        "all_skills": ["React", "Python", "Communication", ...]
    }
    """
    skills_db = load_skills_db()
    text_lower = text.lower()
    
    # 1. Dictionary-based Skill Matching (Categorized)
    found_technical = []
    for skill in skills_db.get("technical", []):
        # We use word boundaries to avoid matching partial strings like "Go" in "Good"
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, text_lower):
            found_technical.append(skill)
            
    found_soft = []
    for skill in skills_db.get("soft", []):
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, text_lower):
            found_soft.append(skill)

    # 2. NER-based Entity Extraction using spaCy
    entities = {}
    nlp = get_spacy_model()
    if nlp:
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ not in entities:
                entities[ent.label_] = []
            
            # Avoid duplicate entities and clean up text
            clean_text = ent.text.strip()
            if clean_text not in entities[ent.label_]:
                entities[ent.label_].append(clean_text)
                
    # 3. Combine for the result
    return {
        "technical": sorted(list(set(found_technical))),
        "soft": sorted(list(set(found_soft))),
        "all_skills": sorted(list(set(found_technical + found_soft))),
        "entities": entities
    }
