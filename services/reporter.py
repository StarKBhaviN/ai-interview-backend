import numpy as np

class InterviewReporter:
    def __init__(self):
        self.weights = {
            "technical": 0.4,
            "communication": 0.4,
            "confidence": 0.2
        }

    def generate_report(self, results: list, warnings: list):
        if not results:
            return self._empty_report()

        # 1. Calculate Fundamental Metrics
        avg_relevance = sum(r.get("relevance_score", 0) for r in results) / len(results)
        avg_confidence = sum(r.get("confidence_score", 0) for r in results) / len(results)
        
        tech_results = [r for r in results if r.get("is_technical", False)]
        avg_tech_relevance = (sum(r.get("relevance_score", 0) for r in tech_results) / len(tech_results)) if tech_results else avg_relevance

        # 2. Derive Category Scores (0-100)
        technical_score = int(avg_tech_relevance * 100)
        communication_score = int(avg_confidence * 100)
        confidence_score = int(avg_confidence * 100)

        # 3. Apply Proctoring Penalties
        warning_count = len(warnings)
        proctoring_penalty = min(25, warning_count * 5)
        
        overall_raw = (technical_score * self.weights["technical"]) + \
                      (communication_score * self.weights["communication"]) + \
                      (confidence_score * self.weights["confidence"])
        
        overall_score = max(0, int(overall_raw - proctoring_penalty))

        # 4. Generate Natural Language Feedback
        strengths = []
        improvements = []

        # Analyze Relevance & Keywords
        all_keywords = []
        for r in results:
            all_keywords.extend(r.get("keywords_found", []))
        unique_keywords = list(set(all_keywords))

        if avg_tech_relevance > 0.75:
            strengths.append(f"Demonstrated deep technical alignment with key mentions of {', '.join(unique_keywords[:3])}.")
        elif avg_tech_relevance < 0.5:
            improvements.append("Strengthen technical depth by providing more specific examples and industry terminology.")

        # Analyze Confidence & Sentiment
        avg_sentiment = self._get_avg_sentiment(results)
        if avg_confidence > 0.8:
            strengths.append("Exhibited consistent vocal clarity and professional confidence throughout the session.")
        elif avg_confidence < 0.6:
            improvements.append("Try to reduce filler words (um, uh) and maintain a more steady speaking pace during complex answers.")

        if avg_sentiment == "Positive":
            strengths.append("Maintained a highly positive and professional tone, which is excellent for team culture.")

        # Analyze Proctoring
        if warning_count > 0:
            improvements.append(f"Ensure a stable environment to avoid proctoring anomalies (detected {warning_count} incidents).")
        else:
            strengths.append("Excellent adherence to interview protocols with zero proctoring flags.")

        # Add more generic but relevant ones if lists are short
        if len(strengths) < 2: strengths.append("Provided structured responses to most behavioral questions.")
        if len(improvements) < 1: improvements.append("Consider elaborating more on your unique contributions in past projects.")

        return {
            "overallScore": overall_score,
            "communicationScore": communication_score,
            "technicalScore": technical_score,
            "confidenceScore": confidence_score,
            "strengths": strengths[:4],
            "improvements": improvements[:4],
            "summary": f"Candidate scored {overall_score}/100 with a strong showing in {self._get_best_category(technical_score, communication_score, confidence_score)}."
        }

    def _get_avg_sentiment(self, results):
        sentiments = [r.get("sentiment", "Neutral") for r in results]
        pos = sentiments.count("Positive")
        neg = sentiments.count("Negative")
        if pos > neg: return "Positive"
        if neg > pos: return "Negative"
        return "Neutral"

    def _get_best_category(self, t, com, con):
        scores = {"Technical": t, "Communication": com, "Confidence": con}
        return max(scores, key=scores.get)

    def _empty_report(self):
        return {
            "overallScore": 0,
            "communicationScore": 0,
            "technicalScore": 0,
            "confidenceScore": 0,
            "strengths": ["Insufficient data"],
            "improvements": ["Complete all interview questions"],
            "summary": "No data available."
        }

reporter = InterviewReporter()
