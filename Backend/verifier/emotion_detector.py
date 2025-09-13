import logging
from transformers import pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load sentiment analysis pipeline once
sentiment_analyzer = pipeline(
	"sentiment-analysis",
	model="distilbert-base-uncased-finetuned-sst-2-english"
)

def detect_emotion(text: str) -> float:
	"""
	Returns a normalized emotion score (0-1) based on sentiment confidence.
	"""
	try:
		result = sentiment_analyzer(text[:512])[0]
		score = result['score']
		logger.info(f"Emotion detected: {result['label']} ({score})")
		return round(score, 2)
	except Exception as e:
		logger.error(f"Emotion detection failed: {e}")
		return 0.0
