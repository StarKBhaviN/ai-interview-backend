from fastapi import APIRouter, UploadFile, File
from ai_models.resume_parser import extract_text_from_pdf, extract_skills

router = APIRouter()

@router.post("/parse-resume")
async def parse_resume(file: UploadFile = File(...)):
    # 1. Extract text using our new parser
    text = extract_text_from_pdf(file.file)
    
    # 2. Extract structured skills and entities using our NLP model
    parse_result = extract_skills(text)
    
    # 3. Return structured data including categorized skills and entities
    return {
        "skills": parse_result.get("all_skills", []),
        "technical": parse_result.get("technical", []),
        "soft": parse_result.get("soft", []),
        "entities": parse_result.get("entities", {}),
        "text_preview": text[:500] if text else ""
    }