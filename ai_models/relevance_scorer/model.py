import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import os

class RelevanceScorer:
    """
    Final inference engine for scoring interview answer relevance.
    It attempts to load a fine-tuned checkpoint from 'checkpoints/'.
    Falls back to 'roberta-base' if no checkpoint is found.
    """
    def __init__(self, model_path=None):
        base_path = os.path.dirname(__file__)
        if model_path is None:
            model_path = os.path.join(base_path, "checkpoints/relevance_model")

        # 1. Check if fine-tuned model exists
        if not os.path.exists(model_path):
            print(f"[RelevanceScorer] checkpoint not found at {model_path}. Loading base 'roberta-base' model.")
            self.model_name = "roberta-base"
        else:
            self.model_name = model_path

        # 2. Load tokenizer and model
        try:
            self.tokenizer = AutoTokenizer.from_pretrained("roberta-base")
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name, 
                num_labels=1
            )
            self.model.eval()
            print(f"[RelevanceScorer] Model loaded successfully: {self.model_name}")
        except Exception as e:
            print(f"[RelevanceScorer] Error loading model: {e}")
            self.model = None

    def score(self, question: str, answer: str) -> float:
        """
        Calculates a relevance score between 0 and 1.
        Uses sigmoid to convert regression output into a probability-like score.
        """
        if self.model is None or not question or not answer:
            return 0.5 # Neutral fallback

        # Truncate to max 512 tokens
        inputs = self.tokenizer(
            question, 
            answer, 
            return_tensors="pt", 
            max_length=512, 
            truncation=True, 
            padding=True
        )

        with torch.no_grad():
            outputs = self.model(**inputs)
        
        # RoBERTa-base with num_labels=1 returns a single scalar logit during regression
        logit = outputs.logits.squeeze().item()
        
        # Convert to 0-1 using sigmoid
        score = torch.sigmoid(torch.tensor(logit)).item()
        return round(score, 3)

# Singleton instance to avoid reloading model for every request
_scorer = None

def get_relevance_scorer():
    global _scorer
    if _scorer is None:
        _scorer = RelevanceScorer()
    return _scorer
