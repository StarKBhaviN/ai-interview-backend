# AI Interview Evaluator — Required Models

This directory contains the weights and configuration for the AI models used in the interview evaluation process.

## Required Models

### 1. Speech-to-Text (STT)
- **Model**: OpenAI Whisper (Small or Medium recommended for local execution)
- **Role**: Converting candidate audio responses into text transcripts for NLP analysis.
- **Implementation**: `openai-whisper` Python package.

### 2. Natural Language Processing (NLP)
- **Model**: RoBERTa-base or BERT-base (Fine-tuned for Sentence Similarity)
- **Role**: Comparing candidate transcripts against "Expected Keywords" and overall question relevance.
- **Metrics**: Keyword coverage, Semantic similarity, Grammar quality.

### 3. Gaze & Face Monitoring (Anti-Cheat)
- **Model**: MediaPipe Face Mesh / Iris
- **Role**: Tracking eye movements (gaze drift), head posture, and person presence.
- **Alerts**: Tab switching (loss of focus), multiple persons, or looking away.

### 4. Audio Sentiment & Tone
- **Model**: Wav2Vec 2.0 or custom Mel-spectrogram CNN
- **Role**: Analyzing pitch, tone, and pause patterns to assess confidence and nervousness.

## Implementation Guide

1.  **Training**: Use Python (PyTorch) for fine-tuning NLP models on domain-specific interview sets.
2.  **Inference**:
    *   **Option A**: Run via FastAPI backend using Python.
    *   **Option B**: Export to **ONNX** and run directly in the Rust (Tauri) backend for lower latency and better distribution.

## Model Versions
- `stt_whisper_small.onnx` (Planned)
- `nlp_relevance_v1.bin` (Planned)
- `face_landmarks_v2.tflite` (Planned)
