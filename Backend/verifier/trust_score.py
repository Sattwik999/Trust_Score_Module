import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_trust_score(face_score: float, doc_score: float, emotion_score: float, engagement_score: float, story_score: float, admin_adjustment: float = 0.0) -> float:
	"""
	Aggregates all sub-scores into a final trust score (0-100).
	Weights can be adjusted for your use case.
	"""
	# All inputs should be normalized (0-1 or 0-20 for story)
	# Example weights (total 1.0):
	weights = {
		'face': 0.2,
		'doc': 0.2,
		'emotion': 0.15,
		'engagement': 0.1,
		'story': 0.25,
		'admin': 0.1
	}
	# Normalize story_score to 0-1 if it's 0-20
	story_score_norm = story_score / 20 if story_score > 1 else story_score
	trust_score = (
		weights['face'] * face_score +
		weights['doc'] * doc_score +
		weights['emotion'] * emotion_score +
		weights['engagement'] * engagement_score +
		weights['story'] * story_score_norm +
		weights['admin'] * admin_adjustment
	) * 100
	trust_score = round(trust_score, 2)
	logger.info(f"Final trust score: {trust_score}")
	return trust_score
