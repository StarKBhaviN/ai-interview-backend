# AI Interview Evaluator - Backend AI Architecture

This directory contains the core intelligence of the platform. Each model is encapsulated as a standalone package with its own logic, training scripts, and data.

## Model Summary

| Model | ID | Technology | Purpose | Implementation |
|-------|----|------------|---------|----------------|
| **Resume Parser** | M1 | spaCy, PyPDF2 | Extracts skills & entities from PDF | `ai_models/resume_parser` |
| **Relevance Scorer** | M2 | RoBERTa-base | NLP Answer-to-Question matching | `ai_models/relevance_scorer` |
| **Confidence Analyzer** | M3 | Librosa, rule-based | Acoustic analysis of candidate tone | `ai_models/confidence_analyzer` |
| **Anti-Cheat Monitor** | M4 | MediaPipe Mesh | Gaze drift & Multi-person detection | `ai_models/anti_cheat` |
| **Speech-to-Text** | STT | Faster-Whisper | High-speed audio transcription | `ai_models/stt` |

## Service Layer

The `services/` directory bridges the AI models with the business logic:
- `evaluation.py`: Fuses all model outputs into a final candidate score (Skill Coverage + Relevance + Performance).
- `question_generator.py`: Dynamically generates interview rounds based on resume skills.
- `reporter.py`: Compiles session data into a professional PDF report.

## Integration Policy

- **Singletons**: All AI models should be accessed via `get_model_name()` methods in their respective `__init__.py` files to prevent redundant memory usage.
- **Async Safety**: Use thread-safe patterns when triggering background training.
- **Fallback**: Inference engines should always provide a heuristic fallback if base models or checkpoints fail to load.
