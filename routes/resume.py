from fastapi import APIRouter, UploadFile, File
from services.pdf_extractor import extract_text_from_pdf
from services.skill_extractor import extract_skills

router = APIRouter()

@router.post("/parse-resume")
async def parse_resume(file: UploadFile = File(...)):
    text = extract_text_from_pdf(file.file)
    skills = extract_skills(text)
    return {"skills": skills}