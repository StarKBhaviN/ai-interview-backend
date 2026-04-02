class EvaluationEngine:
    """
    Calculates final candidate interview scores.
    Combines:
    - Relevance (0.4)
    - Confidence (0.2)
    - Sentiment (0.1)
    - Skill Coverage (0.3)
    """

    def calculate_final_score(self, relevance: float, confidence: float, sentiment: str, matched_skills: list, total_skills: list) -> float:
        # 1. Weights
        W_RELEVANCE = 0.4
        W_CONFIDENCE = 0.2
        W_SKILLS = 0.3
        W_SENTIMENT = 0.1

        # 2. Sentiment Score
        sentiment_score = 0.5
        if sentiment == "Positive" or sentiment == "Confident":
            sentiment_score = 1.0
        elif sentiment == "Negative" or sentiment == "Nervous":
            sentiment_score = 0.2

        # 3. Skill Coverage Score
        skill_coverage = len(matched_skills) / len(total_skills) if total_skills else 0.5
        
        # 4. Final Weighted Calculation
        final = (
            (relevance * W_RELEVANCE) +
            (confidence * W_CONFIDENCE) +
            (skill_coverage * W_SKILLS) +
            (sentiment_score * W_SENTIMENT)
        )

        return round(float(final), 2)

# Singleton
engine = EvaluationEngine()
