# verifier/face_verifier.py
import logging
import cv2
import re
import os
from deepface import DeepFace
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
import xml.etree.ElementTree as ET
from verifier.ocr_verifier import extract_text  # OCR function for Aadhaar/PAN files

# -----------------------
# Logging Setup
# -----------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -----------------------
# Preload model & backend
# -----------------------
MODEL_NAME = "SFace"
DETECTOR_BACKEND = "retinaface"
logger.info(f"Loading face recognition model: {MODEL_NAME}")
model = DeepFace.build_model(MODEL_NAME)
logger.info("Model loaded successfully.")

# -----------------------
# Aadhaar & PAN Validators
# -----------------------
def validate_aadhaar_format(aadhaar_number: str) -> bool:
    """Basic Aadhaar format + Verhoeff checksum"""
    def verhoeff_checksum(num):
        d_table = [
            [0,1,2,3,4,5,6,7,8,9],
            [1,2,3,4,0,6,7,8,9,5],
            [2,3,4,0,1,7,8,9,5,6],
            [3,4,0,1,2,8,9,5,6,7],
            [4,0,1,2,3,9,5,6,7,8],
            [5,9,8,7,6,0,4,3,2,1],
            [6,5,9,8,7,1,0,4,3,2],
            [7,6,5,9,8,2,1,0,4,3],
            [8,7,6,5,9,3,2,1,0,4],
            [9,8,7,6,5,4,3,2,1,0]
        ]
        p_table = [
            [0,1,2,3,4,5,6,7,8,9],
            [1,5,7,6,2,8,3,0,9,4],
            [5,8,0,3,7,9,6,1,4,2],
            [8,9,1,6,0,4,3,5,2,7],
            [9,4,5,3,1,2,6,8,7,0],
            [4,2,8,6,5,7,3,9,0,1],
            [2,7,9,3,8,0,6,4,1,5],
            [7,0,4,6,9,1,3,2,5,8]
        ]
        c = 0
        num = num[::-1]
        for i in range(len(num)):
            c = d_table[c][p_table[i % 8][int(num[i])]]
        return c == 0

    return bool(re.fullmatch(r"\d{12}", aadhaar_number)) and verhoeff_checksum(aadhaar_number)

def verify_aadhaar_offline(xml_or_pdf_path: str, uidai_public_key_path: str) -> bool:
    """Offline Aadhaar XML/QR verification using UIDAI's public key."""
    if not os.path.exists(xml_or_pdf_path) or not os.path.exists(uidai_public_key_path):
        logger.warning("Offline Aadhaar verification skipped: File or public key missing.")
        return False

    try:
        tree = ET.parse(xml_or_pdf_path)
        root = tree.getroot()
        signature = root.attrib.get('signature')
        data = root.attrib.get('data')

        if not signature or not data:
            logger.warning("Signature or data not found in Aadhaar XML.")
            return False

        with open(uidai_public_key_path, "rb") as key_file:
            public_key = serialization.load_pem_public_key(key_file.read())

        public_key.verify(
            bytes.fromhex(signature),
            data.encode(),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        logger.info("✅ Offline Aadhaar signature verification passed.")
        return True

    except Exception as e:
        logger.warning(f"Offline Aadhaar verification failed: {e}")
        return False

def validate_pan(pan_number: str) -> bool:
    return bool(re.fullmatch(r"[A-Z]{5}[0-9]{4}[A-Z]", pan_number))

# -----------------------
# Real Liveness Detection
# -----------------------
def liveness_check(image_path: str, backend: str = DETECTOR_BACKEND) -> float:
    """
    Returns a normalized liveness score (0-1) using DeepFace's confidence.
    """
    try:
        logger.info("Running liveness detection using DeepFace confidence score...")
        result = DeepFace.analyze(img_path=image_path, actions=['emotion'], detector_backend=backend)
        confidence = result[0].get("face_confidence", 0)
        logger.info(f"Liveness confidence: {confidence}")
        # Normalize confidence (assuming max 1.0)
        return min(max(confidence, 0), 1)
    except Exception as e:
        logger.warning(f"Liveness check failed: {e}")
        return 0.0

# -----------------------
# Face Verification Logic
# -----------------------
def verify_face(id_img_path: str, selfie_path: str, aadhaar_number: str, pan_number: str,
                aadhaar_file_path: str = None, pan_file_path: str = None,
                aadhaar_xml_path: str = None, uidai_public_key_path: str = None,
                model_name: str = MODEL_NAME, detector_backend: str = DETECTOR_BACKEND,
                face_threshold: float = 0.4) -> dict:
    """
    Verifies face match + Aadhaar/PAN + optional Aadhaar offline verification + OCR match.
    Returns detailed trust breakdown and total score out of 20.
    """
    trust_score = 0
    result_breakdown = {
        "face_match_score": 0.0,
        "liveness_score": 0.0,
        "aadhaar_valid": False,
        "pan_valid": False,
        "total_score": 0.0,
        "details": {}
    }

    try:
        logger.info("Reading ID and Selfie images...")
        id_img = cv2.imread(id_img_path)
        selfie_img = cv2.imread(selfie_path)
        if id_img is None or selfie_img is None:
            logger.warning("❌ One or both images could not be loaded.")
            return result_breakdown

        logger.info("Running DeepFace verification...")
        result = DeepFace.verify(
            img1_path=id_img_path,
            img2_path=selfie_path,
            model_name=model_name,
            detector_backend=detector_backend,
            enforce_detection=True
        )

        verified = result.get("verified", False)
        distance = result.get("distance", 1.0)
        threshold = face_threshold
        logger.info(f"✅ Match Result: verified={verified}, distance={distance:.4f}, threshold={threshold:.4f}")
        result_breakdown["details"]["distance"] = distance
        result_breakdown["details"]["threshold"] = threshold

        # Normalize face match score (1 for match, 0.5 for near match)
        if verified:
            result_breakdown["face_match_score"] = 1.0
        elif distance <= threshold + 0.1:
            result_breakdown["face_match_score"] = 0.5
        else:
            result_breakdown["face_match_score"] = 0.0

        # Liveness normalized
        liveness = liveness_check(selfie_path, backend=detector_backend)
        result_breakdown["liveness_score"] = liveness
        result_breakdown["details"]["liveness_confidence"] = liveness

        # Aadhaar validation (format + optional offline XML + OCR match if file uploaded)
        basic_aadhaar_valid = validate_aadhaar_format(aadhaar_number)
        offline_verified = False
        if aadhaar_xml_path and uidai_public_key_path:
            offline_verified = verify_aadhaar_offline(aadhaar_xml_path, uidai_public_key_path)

        if basic_aadhaar_valid and (offline_verified or not aadhaar_xml_path):
            if aadhaar_file_path and os.path.exists(aadhaar_file_path):
                text = extract_text(aadhaar_file_path)
                if aadhaar_number in text:
                    result_breakdown["aadhaar_valid"] = True
                    logger.info("✅ Aadhaar number matched in uploaded Aadhaar file.")
                else:
                    logger.warning("❌ Aadhaar number not found in uploaded Aadhaar file.")
            else:
                result_breakdown["aadhaar_valid"] = True
        result_breakdown["details"]["aadhaar_format_valid"] = basic_aadhaar_valid
        result_breakdown["details"]["aadhaar_offline_verified"] = offline_verified

        # PAN validation (regex + OCR match if file uploaded)
        if validate_pan(pan_number):
            if pan_file_path and os.path.exists(pan_file_path):
                text = extract_text(pan_file_path)
                if pan_number in text:
                    result_breakdown["pan_valid"] = True
                    logger.info("✅ PAN number matched in uploaded PAN file.")
                else:
                    logger.warning("❌ PAN number not found in uploaded PAN file.")
            else:
                result_breakdown["pan_valid"] = True
        result_breakdown["details"]["pan_format_valid"] = validate_pan(pan_number)

        # Final trust score (normalized, out of 1)
        trust_score = (
            0.7 * result_breakdown["face_match_score"] +
            0.3 * result_breakdown["liveness_score"]
        )
        result_breakdown["total_score"] = round(trust_score, 2)
        logger.info(f"Face verification breakdown: {result_breakdown}")
        return result_breakdown

    except ValueError as ve:
        logger.error(f"❌ Face not detected in one of the images: {ve}")
        return result_breakdown
    except Exception as e:
        logger.error(f"❌ Error during face verification: {e}")
        return result_breakdown

# # verifier/face_verifier.py
# import logging
# import cv2
# import re
# import os
# from deepface import DeepFace
# from cryptography.hazmat.primitives import serialization, hashes
# from cryptography.hazmat.primitives.asymmetric import padding
# import xml.etree.ElementTree as ET

# # -----------------------
# # Logging Setup
# # -----------------------
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # -----------------------
# # Preload model & backend
# # -----------------------
# MODEL_NAME = "SFace"
# DETECTOR_BACKEND = "retinaface"
# logger.info(f"Loading face recognition model: {MODEL_NAME}")
# model = DeepFace.build_model(MODEL_NAME)
# logger.info("Model loaded successfully.")

# # -----------------------
# # Aadhaar & PAN Validators
# # -----------------------
# def validate_aadhaar_format(aadhaar_number: str) -> bool:
#     """Basic Aadhaar format + Verhoeff checksum"""
#     def verhoeff_checksum(num):
#         d_table = [
#             [0,1,2,3,4,5,6,7,8,9],
#             [1,2,3,4,0,6,7,8,9,5],
#             [2,3,4,0,1,7,8,9,5,6],
#             [3,4,0,1,2,8,9,5,6,7],
#             [4,0,1,2,3,9,5,6,7,8],
#             [5,9,8,7,6,0,4,3,2,1],
#             [6,5,9,8,7,1,0,4,3,2],
#             [7,6,5,9,8,2,1,0,4,3],
#             [8,7,6,5,9,3,2,1,0,4],
#             [9,8,7,6,5,4,3,2,1,0]
#         ]
#         p_table = [
#             [0,1,2,3,4,5,6,7,8,9],
#             [1,5,7,6,2,8,3,0,9,4],
#             [5,8,0,3,7,9,6,1,4,2],
#             [8,9,1,6,0,4,3,5,2,7],
#             [9,4,5,3,1,2,6,8,7,0],
#             [4,2,8,6,5,7,3,9,0,1],
#             [2,7,9,3,8,0,6,4,1,5],
#             [7,0,4,6,9,1,3,2,5,8]
#         ]
#         c = 0
#         num = num[::-1]
#         for i in range(len(num)):
#             c = d_table[c][p_table[i % 8][int(num[i])]]
#         return c == 0

#     return bool(re.fullmatch(r"\d{12}", aadhaar_number)) and verhoeff_checksum(aadhaar_number)


# def verify_aadhaar_offline(xml_or_pdf_path: str, uidai_public_key_path: str) -> bool:
#     """
#     Offline Aadhaar XML/QR verification using UIDAI's public key.
#     Returns True if signature is valid, else False.
#     """
#     if not os.path.exists(xml_or_pdf_path) or not os.path.exists(uidai_public_key_path):
#         logger.warning("Offline Aadhaar verification skipped: File or public key missing.")
#         return False

#     try:
#         # Parse Aadhaar XML (from QR code or UIDAI offline KYC ZIP extraction)
#         tree = ET.parse(xml_or_pdf_path)
#         root = tree.getroot()
#         signature = root.attrib.get('signature')
#         data = root.attrib.get('data')

#         if not signature or not data:
#             logger.warning("Signature or data not found in Aadhaar XML.")
#             return False

#         # Load UIDAI public key
#         with open(uidai_public_key_path, "rb") as key_file:
#             public_key = serialization.load_pem_public_key(key_file.read())

#         # Verify UIDAI's digital signature
#         public_key.verify(
#             bytes.fromhex(signature),
#             data.encode(),
#             padding.PKCS1v15(),
#             hashes.SHA256()
#         )
#         logger.info("✅ Offline Aadhaar signature verification passed.")
#         return True

#     except Exception as e:
#         logger.warning(f"Offline Aadhaar verification failed: {e}")
#         return False


# def validate_pan(pan_number: str) -> bool:
#     return bool(re.fullmatch(r"[A-Z]{5}[0-9]{4}[A-Z]", pan_number))


# # -----------------------
# # Real Liveness Detection
# # -----------------------
# def liveness_check(image_path: str) -> bool:
#     try:
#         logger.info("Running liveness detection using SFace confidence score...")
#         result = DeepFace.analyze(img_path=image_path, actions=['emotion'], detector_backend=DETECTOR_BACKEND)
#         confidence = result[0].get("face_confidence", 0)
#         logger.info(f"Liveness confidence: {confidence}")
#         return confidence > 0.95
#     except Exception as e:
#         logger.warning(f"Liveness check failed: {e}")
#         return False


# # -----------------------
# # Face Verification Logic
# # -----------------------
# def verify_face(id_img_path: str, selfie_path: str, aadhaar_number: str, pan_number: str,
#                 aadhaar_xml_path: str = None, uidai_public_key_path: str = None) -> dict:
#     """
#     Verifies face match + Aadhaar/PAN + optional Aadhaar offline verification.
#     Returns detailed trust breakdown and total score out of 20.
#     """
#     trust_score = 0
#     result_breakdown = {
#         "face_match_score": 0,
#         "liveness_score": 0,
#         "aadhaar_valid": False,
#         "pan_valid": False,
#         "total_score": 0
#     }

#     try:
#         logger.info("Reading ID and Selfie images...")
#         id_img = cv2.imread(id_img_path)
#         selfie_img = cv2.imread(selfie_path)
#         if id_img is None or selfie_img is None:
#             logger.warning("❌ One or both images could not be loaded.")
#             return result_breakdown

#         logger.info("Running DeepFace verification...")
#         result = DeepFace.verify(
#             img1_path=id_img_path,
#             img2_path=selfie_path,
#             model_name=MODEL_NAME,
#             detector_backend=DETECTOR_BACKEND,
#             enforce_detection=True
#         )

#         verified = result.get("verified", False)
#         distance = result.get("distance", 1.0)
#         threshold = result.get("threshold", 0.4)
#         logger.info(f"✅ Match Result: verified={verified}, distance={distance:.4f}, threshold={threshold:.4f}")

#         if verified:
#             result_breakdown["face_match_score"] = 15
#         elif distance <= threshold + 0.1:
#             result_breakdown["face_match_score"] = 10

#         if liveness_check(selfie_path):
#             result_breakdown["liveness_score"] = 5

#         # Aadhaar validation
#         basic_aadhaar_valid = validate_aadhaar_format(aadhaar_number)
#         offline_verified = False
#         if aadhaar_xml_path and uidai_public_key_path:
#             offline_verified = verify_aadhaar_offline(aadhaar_xml_path, uidai_public_key_path)

#         result_breakdown["aadhaar_valid"] = basic_aadhaar_valid and (offline_verified or not aadhaar_xml_path)
#         if result_breakdown["aadhaar_valid"]:
#             trust_score += 2.5

#         # PAN validation
#         result_breakdown["pan_valid"] = validate_pan(pan_number)
#         if result_breakdown["pan_valid"]:
#             trust_score += 2.5

#         # Total trust score
#         trust_score += result_breakdown["face_match_score"]
#         trust_score += result_breakdown["liveness_score"]
#         result_breakdown["total_score"] = round(trust_score)

#         return result_breakdown

#     except ValueError as ve:
#         logger.error(f"❌ Face not detected in one of the images: {ve}")
#         return result_breakdown
#     except Exception as e:
#         logger.error(f"❌ Error during face verification: {e}")
#         return result_breakdown

# # verifier/face_verifier.py

# import logging
# import cv2
# import re
# from deepface import DeepFace

# # -----------------------
# # Logging Setup
# # -----------------------
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # -----------------------
# # Preload model & backend
# # -----------------------
# MODEL_NAME = "SFace"
# DETECTOR_BACKEND = "retinaface"

# logger.info(f"Loading face recognition model: {MODEL_NAME}")
# model = DeepFace.build_model(MODEL_NAME)
# logger.info("Model loaded successfully.")

# # -----------------------
# # Aadhaar and PAN Validators
# # -----------------------
# def validate_aadhaar(aadhaar_number: str) -> bool:
#     def verhoeff_checksum(num):
#         d_table = [
#             [0,1,2,3,4,5,6,7,8,9],
#             [1,2,3,4,0,6,7,8,9,5],
#             [2,3,4,0,1,7,8,9,5,6],
#             [3,4,0,1,2,8,9,5,6,7],
#             [4,0,1,2,3,9,5,6,7,8],
#             [5,9,8,7,6,0,4,3,2,1],
#             [6,5,9,8,7,1,0,4,3,2],
#             [7,6,5,9,8,2,1,0,4,3],
#             [8,7,6,5,9,3,2,1,0,4],
#             [9,8,7,6,5,4,3,2,1,0]
#         ]

#         p_table = [
#             [0,1,2,3,4,5,6,7,8,9],
#             [1,5,7,6,2,8,3,0,9,4],
#             [5,8,0,3,7,9,6,1,4,2],
#             [8,9,1,6,0,4,3,5,2,7],
#             [9,4,5,3,1,2,6,8,7,0],
#             [4,2,8,6,5,7,3,9,0,1],
#             [2,7,9,3,8,0,6,4,1,5],
#             [7,0,4,6,9,1,3,2,5,8]
#         ]

#         c = 0
#         num = num[::-1]
#         for i in range(len(num)):
#             c = d_table[c][p_table[i % 8][int(num[i])]]
#         return c == 0

#     return bool(re.fullmatch(r"\d{12}", aadhaar_number)) and verhoeff_checksum(aadhaar_number)

# def validate_pan(pan_number: str) -> bool:
#     return bool(re.fullmatch(r"[A-Z]{5}[0-9]{4}[A-Z]", pan_number))

# # -----------------------
# # Real Liveness Detection
# # -----------------------
# def liveness_check(image_path: str) -> bool:
#     try:
#         logger.info("Running liveness detection using SFace confidence score...")
#         result = DeepFace.analyze(img_path=image_path, actions=['emotion'], detector_backend=DETECTOR_BACKEND)
#         confidence = result[0].get("face_confidence", 0)
#         logger.info(f"Liveness confidence: {confidence}")
#         return confidence > 0.95
#     except Exception as e:
#         logger.warning(f"Liveness check failed: {e}")
#         return False

# # -----------------------
# # Face Verification Logic with Trust Scoring
# # -----------------------
# def verify_face(id_img_path: str, selfie_path: str, aadhaar_number: str, pan_number: str) -> dict:
#     """
#     Verifies the face and validates Aadhaar/PAN formats.
#     Returns detailed trust breakdown and total score out of 20.
#     """
#     trust_score = 0
#     result_breakdown = {
#         "face_match_score": 0,
#         "liveness_score": 0,
#         "aadhaar_valid": False,
#         "pan_valid": False,
#         "total_score": 0
#     }

#     try:
#         logger.info("Reading ID and Selfie images...")
#         id_img = cv2.imread(id_img_path)
#         selfie_img = cv2.imread(selfie_path)

#         if id_img is None or selfie_img is None:
#             logger.warning("❌ One or both images could not be loaded.")
#             return result_breakdown

#         logger.info("Running DeepFace verification...")
#         result = DeepFace.verify(
#             img1_path=id_img_path,
#             img2_path=selfie_path,
#             model_name=MODEL_NAME,
#             detector_backend=DETECTOR_BACKEND,
#             enforce_detection=True
#         )

#         verified = result.get("verified", False)
#         distance = result.get("distance", 1.0)
#         threshold = result.get("threshold", 0.4)

#         logger.info(f"✅ Match Result: verified={verified}, distance={distance:.4f}, threshold={threshold:.4f}")

#         if verified:
#             result_breakdown["face_match_score"] = 15
#         elif distance <= threshold + 0.1:
#             result_breakdown["face_match_score"] = 10

#         if liveness_check(selfie_path):
#             result_breakdown["liveness_score"] = 5

#         result_breakdown["aadhaar_valid"] = validate_aadhaar(aadhaar_number)
#         if result_breakdown["aadhaar_valid"]:
#             trust_score += 2.5

#         result_breakdown["pan_valid"] = validate_pan(pan_number)
#         if result_breakdown["pan_valid"]:
#             trust_score += 2.5

#         trust_score += result_breakdown["face_match_score"]
#         trust_score += result_breakdown["liveness_score"]
#         result_breakdown["total_score"] = round(trust_score)

#         return result_breakdown

#     except ValueError as ve:
#         logger.error(f"❌ Face not detected in one of the images: {ve}")
#         return result_breakdown

#     except Exception as e:
#         logger.error(f"❌ Error during face verification: {e}")
#         return result_breakdown

# # verifier/face_verifier.py

# import logging
# import cv2
# from deepface import DeepFace

# # -----------------------
# # Logging Setup
# # -----------------------
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # -----------------------
# # Preload model & backend
# # -----------------------
# MODEL_NAME = "Facenet512"  # You can change to 'Facenet', 'ArcFace', 'Dlib', etc.
# DETECTOR_BACKEND = "retinaface"  # Or use: 'opencv', 'ssd', 'mtcnn'

# logger.info(f"Loading face recognition model: {MODEL_NAME}")
# model = DeepFace.build_model(MODEL_NAME)
# logger.info("Model loaded successfully.")

# # -----------------------
# # Face Verification Logic
# # -----------------------
# def verify_face(id_img_path: str, selfie_path: str) -> int:
#     """
#     Verifies if the face in ID matches the face in selfie.
#     Returns a score out of 20.
#     """
#     try:
#         logger.info("Reading ID and Selfie images...")

#         # Load images using OpenCV
#         id_img = cv2.imread(id_img_path)
#         selfie_img = cv2.imread(selfie_path)

#         if id_img is None or selfie_img is None:
#             logger.warning("❌ One or both images could not be loaded.")
#             return 0

#         logger.info("Running DeepFace verification...")
#         result = DeepFace.verify(
#             img1_path=id_img_path,
#             img2_path=selfie_path,
#             model_name=MODEL_NAME,
#             detector_backend=DETECTOR_BACKEND,
#             enforce_detection=True
#         )

#         verified = result.get("verified", False)
#         distance = result.get("distance", 1.0)
#         threshold = result.get("threshold", 0.4)

#         logger.info(f"✅ Match Result: verified={verified}, distance={distance:.4f}, threshold={threshold:.4f}")

#         # Simple scoring logic
#         if verified:
#             return 20
#         elif distance <= threshold + 0.1:
#             return 10
#         else:
#             return 0

#     except ValueError as ve:
#         logger.error(f"❌ Face not detected in one of the images: {ve}")
#         return 0

#     except Exception as e:
#         logger.error(f"❌ Error during face verification: {e}")
#         return 0
