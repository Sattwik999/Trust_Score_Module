# verifier/story_nlp.py
import re
import textstat
from transformers import pipeline

class StoryNLPVerifier:
    def __init__(self):
        # Load Hugging Face pipelines once at startup
        self.sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english"
        )
        self.auth_classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli"
        )
        self.fraud_keywords = [
            "guarantee returns", "double your money", "urgent investment",
            "lottery", "inheritance", "100% safe", "get rich quick"
        ]

    def check_readability(self, text: str) -> float:
        """Score readability (0–10)."""
        score = textstat.flesch_reading_ease(text)
        return max(0, min(10, score / 10))

    def check_authenticity(self, text: str) -> float:
        """Score authenticity (0–5)."""
        labels = ["genuine", "fake"]
        result = self.auth_classifier(text, candidate_labels=labels)
        genuine_score = result['scores'][result['labels'].index("genuine")]
        return round(genuine_score * 5, 2)

    def check_emotional_appeal(self, text: str) -> float:
        """Score emotional intensity (0–5)."""
        result = self.sentiment_analyzer(text[:512])[0]
        if result['label'].upper() in ["POSITIVE", "NEGATIVE"]:
            return round(result['score'] * 5, 2)
        return 0.0

    def check_fraud_markers(self, text: str) -> int:
        """Return fraud penalty (-5 to 0)."""
        penalty = 0
        for keyword in self.fraud_keywords:
            if re.search(rf"\b{re.escape(keyword)}\b", text, re.IGNORECASE):
                penalty -= 1
        return max(-5, penalty)

    def score_story(self, text: str) -> float:
        """Total story quality score (0–20)."""
        readability = self.check_readability(text)       # 0–10
        authenticity = self.check_authenticity(text)     # 0–5
        emotion = self.check_emotional_appeal(text)      # 0–5
        fraud_penalty = self.check_fraud_markers(text)   # -5 to 0
        total = readability + authenticity + emotion + fraud_penalty
        return round(max(0, min(20, total)), 2)
