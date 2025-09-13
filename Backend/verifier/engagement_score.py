import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_engagement_score(story: str) -> float:
	"""
	Returns a normalized engagement score (0-1) based on story length and keyword presence.
	"""
	min_length = 100
	max_length = 1000
	length_score = min(max(len(story), min_length), max_length) / max_length

	# Engagement keywords (customize as needed)
	keywords = ["challenge", "achievement", "motivation", "impact", "community"]
	keyword_hits = sum(1 for kw in keywords if kw.lower() in story.lower())
	keyword_score = keyword_hits / len(keywords)

	# Weighted average
	engagement_score = round(0.7 * length_score + 0.3 * keyword_score, 2)
	logger.info(f"Engagement score: {engagement_score} (length: {length_score}, keywords: {keyword_score})")
	return engagement_score
