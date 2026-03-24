# AI Interview Evaluator — AI Strategy & Training

This document outlines how to implement, train, and run the AI models for this project.

## 1. Technical Implementation (Python + FastAPI)
We use Python for AI because of its mature ecosystem (PyTorch, HuggingFace, MediaPipe). FastAPI provides a high-performance bridge between the Next.js/Rust frontend and the heavy AI models.

### Setup
1. **Environment**: Use `conda` or `venv` with Python 3.10+.
2. **Key Libraries**:
   - `openai-whisper`: For Speech-to-Text.
   - `transformers`: For BERT/RoBERTa (NLP analysis).
   - `mediapipe`: For real-time gaze tracking and person detection.
   - `librosa`: For audio features (pitch, jitters).

## 2. Model Training Strategy

### Speech-to-Text (STT)
- **Model**: OpenAI Whisper (Base or Small).
- **Strategy**: No training needed; Whisper is robust out-of-the-box. Use `faster-whisper` for optimized inference.

### NLP Content Analysis (Relevance)
- **Model**: RoBERTa-base.
- **Training**: Fine-tune on a custom dataset of (Question, Answer, Score 0-1).
- **Tools**: HuggingFace `Trainer` API.
- **Dataset**: Can be synthesised using GPT-4 to generate examples of "good" vs "bad" answers to technical interview questions.

### Confidence & Tone Analysis
- **Model**: Wav2Vec 2.0 or Huber.
- **Training**: Use the **RECOLA** or **IEMOCAP** datasets for sentiment/arousal/valence.
- **Features**: Extract prosodic features (pitch, intensity, duration of speech vs silence).

### Anti-Cheating (Gaze/Face)
- **Model**: MediaPipe Face Mesh.
- **Strategy**: Use geometric calculations to detect gaze direction (out of screen) and person count. No custom training required.

## 3. Running the Models
1. **Development**: Run `python main.py` to start the FastAPI server.
2. **Production**: Use **ONNX Runtime** or **TensorRT** for faster inference on CPU/GPU.
3. **Rust Integration**: The Tauri backend can call the FastAPI endpoints or directly load ONNX models using `ort` (ONNX Runtime Rust bindings).

---
**Recommendation**: Start with the FastAPI bridge for rapid prototyping, then move to ONNX for lower latency.
