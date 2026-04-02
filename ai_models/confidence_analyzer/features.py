import librosa
import numpy as np
import os

def extract_audio_features(audio_path: str) -> dict:
    """
    Extracts high-level acoustic features from an audio file.
    Specifically: Pitch, Energy (RMS), Zero-Crossing Rate, and Silence Ratio.
    """
    if not os.path.exists(audio_path):
        print(f"[features.py] Audio file not found: {audio_path}")
        return {}

    try:
        # Load audio (16kHz for consistency)
        y, sr = librosa.load(audio_path, sr=16000)
        
        if len(y) == 0:
            return {}

        # 1. Pitch Extraction (Mean Pitch in Hz)
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        # Select pitch with highest magnitude for each frame
        pitch_vals = []
        for i in range(pitches.shape[1]):
            index = magnitudes[:, i].argmax()
            p = pitches[index, i]
            if p > 0:
                pitch_vals.append(p)
        
        pitch_mean = np.mean(pitch_vals) if pitch_vals else 0
        
        # 2. Energy / Volume (RMS)
        rms = librosa.feature.rms(y=y)[0]
        energy_mean = np.mean(rms)
        
        # 3. Speaking Rate Approximation (Zero-Crossing Rate)
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        zcr_mean = np.mean(zcr)
        
        # 4. Pause Detection (Silence Ratio)
        # Split speech into non-silent intervals
        intervals = librosa.effects.split(y, top_db=30)
        total_speech_samples = sum(end - start for start, end in intervals)
        silence_ratio = 1.0 - (total_speech_samples / len(y)) if len(y) > 0 else 0
        
        # 5. Mel-spectrogram (Fixed size for future CNN input if needed)
        mel_spec = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128)
        
        return {
            "pitch_mean": float(pitch_mean),
            "energy_mean": float(energy_mean),
            "zcr_mean": float(zcr_mean),
            "silence_ratio": float(silence_ratio),
            "duration": float(len(y) / sr)
        }
    except Exception as e:
        print(f"[features.py] Error extracting features: {e}")
        return {}
