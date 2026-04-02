# Model 1: Resume Skill Extractor

## Technology Stack
- **Python**: Core logic.
- **spaCy**: Natural Language Processing (NER, Text Segregation).
- **PyPDF2**: PDF text extraction.
- **JSON**: Dictionary-based matching.

## Purpose
This component extracts structured data from PDF resumes, including:
- **Technical Skills**: Languages, frameworks, databases, and tools.
- **Soft Skills**: Interpersonal and organizational traits.
- **Entities**: Organizations (ORG), Locations (GPE), and Dates (DATE).

## Folder Structure
- `parser.py`: Handles file-to-text conversion.
- `skill_extractor.py`: Core NLP logic using `spaCy` and `skills_db.json`.
- `skills_db.json`: Taxonomy of known skills.

## Usage
```python
from ai_models.resume_parser import extract_text_from_pdf, extract_skills

# 1. Get raw text
text = extract_text_from_pdf(file_path_or_stream)

# 2. Get structured skills
data = extract_skills(text)
print(data['technical'])
print(data['entities'])
```
