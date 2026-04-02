# backend/ai_models/resume_parser/__init__.py
from .parser import extract_text_from_pdf
from .skill_extractor import extract_skills

__all__ = ["extract_text_from_pdf", "extract_skills"]
