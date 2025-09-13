from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import logging
from flask_cors import CORS

# Import verification functions
from verifier.face_verifier import verify_face
from verifier.ocr_verifier import verify_supporting_document
from verifier.story_nlp import StoryNLPVerifier
from verifier.emotion_detector import detect_emotion
from verifier.engagement_score import calculate_engagement_score
from verifier.trust_score import calculate_trust_score
from models import db, TrustScoreRecord

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app setup
app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trustscores.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Story NLP Verifier instance
story_verifier = StoryNLPVerifier()

# Home route to avoid 404
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "🚀 Welcome to AIKYA the Trust Score API!",
        "endpoints": {
            "submit": "/submit [POST]",
            "records": "/records [GET]"
        }
    })

# Trust Score Calculation
def calculate_trust_score(story, face_score, doc_score, emotion_score, engagement_score, admin_adjustment):
    story_score = min(len(story) / 20, 25)  # Max story weight is 25
    trust_score = round(
        0.2 * face_score +
        0.2 * doc_score +
        0.15 * emotion_score +
        0.25 * story_score +
        0.1 * engagement_score +
        0.1 * admin_adjustment,
        2
    )
    return trust_score

@app.route('/submit', methods=['POST'])
def submit():
    try:
        # Extract form data
        required_fields = ['name', 'story', 'supporting_doc_type', 'aadhaar_number', 'pan_number', 'user_id']
        form_data = {}
        missing_fields = []

        for field in required_fields:
            value = request.form.get(field)
            if not value:
                missing_fields.append(field)
            form_data[field] = value

        # Extract files
        required_files = {
            'id_image': None,
            'selfie_image': None,
            'supporting_doc': None,
            'aadhaar_doc': None,
            'pan_doc': None
        }
        for file_key in required_files.keys():
            file_obj = request.files.get(file_key)
            if not file_obj:
                missing_fields.append(file_key)
            required_files[file_key] = file_obj

        # If any field/file missing, return error
        if missing_fields:
            logger.warning(f"Missing required fields/files: {missing_fields}")
            return jsonify(error=f"Missing required fields/files: {missing_fields}"), 400

        # Save uploaded files
        upload_dir = "temp"
        os.makedirs(upload_dir, exist_ok=True)

        id_path = os.path.join(upload_dir, f"{form_data['name']}_id.jpg")
        selfie_path = os.path.join(upload_dir, f"{form_data['name']}_selfie.jpg")
        doc_path = os.path.join(upload_dir, f"{form_data['name']}_{form_data['supporting_doc_type']}.pdf")
        aadhaar_path = os.path.join(upload_dir, f"{form_data['name']}_aadhaar.jpg")
        pan_path = os.path.join(upload_dir, f"{form_data['name']}_pan.jpg")

        required_files['id_image'].save(id_path)
        required_files['selfie_image'].save(selfie_path)
        required_files['supporting_doc'].save(doc_path)
        required_files['aadhaar_doc'].save(aadhaar_path)
        required_files['pan_doc'].save(pan_path)

        logger.info("✔️ All images and documents saved.")

        # Run verifications
        face_result = verify_face(
            id_path, selfie_path,
            form_data['aadhaar_number'], form_data['pan_number'],
            aadhaar_file_path=aadhaar_path,
            pan_file_path=pan_path
        )
        face_score = face_result.get("total_score", 0)
        face_match = face_score >= 5

        doc_score = verify_supporting_document(doc_path, form_data['supporting_doc_type'])
        document_verified = doc_score >= 10


        # Emotion score (NLP sentiment)
        emotion_score = detect_emotion(form_data['story'])

        # Engagement score
        engagement_score = calculate_engagement_score(form_data['story'])

        # Story score (quality, authenticity, etc.)
        story_score = story_verifier.score_story(form_data['story'])

        # Admin adjustment (default 0)
        admin_adjustment = 0.0

        # Final trust score (aggregated)
        trust_score = calculate_trust_score(
            face_score, doc_score, emotion_score, engagement_score, story_score, admin_adjustment
        )

        # Save to DB
        record = TrustScoreRecord(
            user_id=form_data['user_id'],
            name=form_data['name'],
            story=form_data['story'],
            trust_score=trust_score,
            face_match=face_match,
            document_verified=document_verified,
            emotion_score=emotion_score,
            engagement_score=engagement_score,
            admin_adjustment=admin_adjustment,
            id_image_path=id_path,
            selfie_image_path=selfie_path,
            supporting_doc_type=form_data['supporting_doc_type'],
            supporting_doc_path=doc_path,
            supporting_doc_score=doc_score,
            aadhaar_number=form_data['aadhaar_number'],
            pan_number=form_data['pan_number'],
            aadhaar_file_path=aadhaar_path,
            pan_file_path=pan_path
        )

        db.session.add(record)
        db.session.commit()
        logger.info(f"✅ Trust score saved for user: {form_data['name']}")

        return jsonify({
            "message": "✅ Trust score generated successfully",
            "user_id": form_data['user_id'],
            "name": form_data['name'],
            "trust_score": trust_score,
            "face_match": face_match,
            "document_verified": document_verified,
            "story_score": emotion_score
        })

    except Exception as e:
        logger.error(f"❌ Error in /submit: {e}", exc_info=True)
        return jsonify(error="An internal error occurred. Please try again later."), 500

@app.route('/records', methods=['GET'])
def get_records():
    try:
        records = TrustScoreRecord.query.all()
        result = []
        for r in records:
            result.append({
                "id": r.id,
                "user_id": r.user_id,
                "name": r.name,
                "story": r.story,
                "trust_score": r.trust_score,
                "face_match": r.face_match,
                "document_verified": r.document_verified,
                "emotion_score": r.emotion_score,
                "engagement_score": r.engagement_score,
                "admin_adjustment": r.admin_adjustment,
                "id_image_path": r.id_image_path,
                "selfie_image_path": r.selfie_image_path,
                "aadhaar_number": r.aadhaar_number,
                "pan_number": r.pan_number,
                "aadhaar_file_path": r.aadhaar_file_path,
                "pan_file_path": r.pan_file_path,
                "supporting_doc_type": r.supporting_doc_type,
                "supporting_doc_path": r.supporting_doc_path,
                "supporting_doc_score": r.supporting_doc_score,
                "created_at": r.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        return jsonify(records=result)
    except Exception as e:
        logger.error(f"❌ Error fetching records: {e}", exc_info=True)
        return jsonify(error="Failed to fetch records."), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    logger.info("🚀 Trust Score API is running at http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)

# from flask import Flask, request, jsonify
# from flask_sqlalchemy import SQLAlchemy
# import os
# import logging

# # Import verification functions
# from verifier.face_verifier import verify_face
# from verifier.ocr_verifier import verify_supporting_document
# from verifier.story_nlp import StoryNLPVerifier  # ✅ NEW IMPORT
# from models import db, TrustScoreRecord

# # Logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Flask app setup
# app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trustscores.db'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# db.init_app(app)

# # Story NLP Verifier instance
# story_verifier = StoryNLPVerifier()

# # Trust Score Calculation
# def calculate_trust_score(story, face_score, doc_score, emotion_score, engagement_score, admin_adjustment):
#     story_score = min(len(story) / 20, 25)  # Max story weight is 25
#     trust_score = round(
#         0.2 * face_score +
#         0.2 * doc_score +
#         0.15 * emotion_score +
#         0.25 * story_score +
#         0.1 * engagement_score +
#         0.1 * admin_adjustment,
#         2
#     )
#     return trust_score

# @app.route('/submit', methods=['POST'])
# def submit():
#     try:
#         # Extract form data
#         name = request.form.get('name')
#         story = request.form.get('story')
#         doc_type = request.form.get('supporting_doc_type')
#         aadhaar_number = request.form.get('aadhaar_number')
#         pan_number = request.form.get('pan_number')
#         user_id = request.form.get('user_id')

#         id_img = request.files.get('id_image')
#         selfie_img = request.files.get('selfie_image')
#         supporting_doc = request.files.get('supporting_doc')
#         aadhaar_doc = request.files.get('aadhaar_doc')
#         pan_doc = request.files.get('pan_doc')

#         # Check missing fields
#         if not all([name, story, doc_type, id_img, selfie_img, supporting_doc, aadhaar_number, pan_number, user_id, aadhaar_doc, pan_doc]):
#             return jsonify(error="Missing required fields or files"), 400

#         # Save uploaded files
#         upload_dir = "temp"
#         os.makedirs(upload_dir, exist_ok=True)

#         id_path = os.path.join(upload_dir, f"{name}_id.jpg")
#         selfie_path = os.path.join(upload_dir, f"{name}_selfie.jpg")
#         doc_path = os.path.join(upload_dir, f"{name}_{doc_type}.pdf")
#         aadhaar_path = os.path.join(upload_dir, f"{name}_aadhaar.jpg")
#         pan_path = os.path.join(upload_dir, f"{name}_pan.jpg")

#         id_img.save(id_path)
#         selfie_img.save(selfie_path)
#         supporting_doc.save(doc_path)
#         aadhaar_doc.save(aadhaar_path)
#         pan_doc.save(pan_path)

#         logger.info("✔️ All images and documents saved.")

#         # Run verifications
#         face_result = verify_face(
#             id_path, selfie_path,
#             aadhaar_number, pan_number,
#             aadhaar_file_path=aadhaar_path,
#             pan_file_path=pan_path
#         )
#         face_score = face_result.get("total_score", 0)
#         face_match = face_score >= 5

#         doc_score = verify_supporting_document(doc_path, doc_type)
#         document_verified = doc_score >= 10

#         # ✅ Get actual NLP story score
#         emotion_score = story_verifier.score_story(story)

#         # Placeholder for engagement & admin adjustment
#         engagement_score = 7.5
#         admin_adjustment = 0.0

#         # Final trust score
#         trust_score = calculate_trust_score(
#             story, face_score, doc_score, emotion_score, engagement_score, admin_adjustment
#         )

#         # Save to DB
#         record = TrustScoreRecord(
#             user_id=user_id,
#             name=name,
#             story=story,
#             trust_score=trust_score,
#             face_match=face_match,
#             document_verified=document_verified,
#             emotion_score=emotion_score,
#             engagement_score=engagement_score,
#             admin_adjustment=admin_adjustment,
#             id_image_path=id_path,
#             selfie_image_path=selfie_path,
#             supporting_doc_type=doc_type,
#             supporting_doc_path=doc_path,
#             supporting_doc_score=doc_score,
#             aadhaar_number=aadhaar_number,
#             pan_number=pan_number,
#             aadhaar_file_path=aadhaar_path,
#             pan_file_path=pan_path
#         )

#         db.session.add(record)
#         db.session.commit()

#         logger.info(f"✅ Trust score saved for user: {name}")

#         return jsonify({
#             "message": "✅ Trust score generated successfully",
#             "user_id": user_id,
#             "name": name,
#             "trust_score": trust_score,
#             "face_match": face_match,
#             "document_verified": document_verified,
#             "story_score": emotion_score
#         })

#     except Exception as e:
#         logger.error(f"❌ Error in /submit: {e}")
#         return jsonify(error="An internal error occurred. Please try again later."), 500

# @app.route('/records', methods=['GET'])
# def get_records():
#     try:
#         records = TrustScoreRecord.query.all()
#         result = []
#         for r in records:
#             result.append({
#                 "id": r.id,
#                 "user_id": r.user_id,
#                 "name": r.name,
#                 "story": r.story,
#                 "trust_score": r.trust_score,
#                 "face_match": r.face_match,
#                 "document_verified": r.document_verified,
#                 "emotion_score": r.emotion_score,
#                 "engagement_score": r.engagement_score,
#                 "admin_adjustment": r.admin_adjustment,
#                 "id_image_path": r.id_image_path,
#                 "selfie_image_path": r.selfie_image_path,
#                 "aadhaar_number": r.aadhaar_number,
#                 "pan_number": r.pan_number,
#                 "aadhaar_file_path": r.aadhaar_file_path,
#                 "pan_file_path": r.pan_file_path,
#                 "supporting_doc_type": r.supporting_doc_type,
#                 "supporting_doc_path": r.supporting_doc_path,
#                 "supporting_doc_score": r.supporting_doc_score,
#                 "created_at": r.created_at.strftime('%Y-%m-%d %H:%M:%S')
#             })
#         return jsonify(records=result)
#     except Exception as e:
#         logger.error(f"❌ Error fetching records: {e}")
#         return jsonify(error="Failed to fetch records."), 500

# if __name__ == '__main__':
#     with app.app_context():
#         db.create_all()
#     logger.info("🚀 Trust Score API is running at http://127.0.0.1:5000")
#     app.run(debug=True)

# from flask import Flask, request, jsonify
# from flask_sqlalchemy import SQLAlchemy
# import os
# import logging

# # Import verification functions
# from verifier.face_verifier import verify_face
# from verifier.ocr_verifier import verify_supporting_document
# from models import db, TrustScoreRecord

# # -----------------------
# # Logging Setup
# # -----------------------
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # -----------------------
# # App & DB Setup
# # -----------------------
# app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trustscores.db'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# db.init_app(app)

# # -----------------------
# # Trust Score Calculation
# # -----------------------
# def calculate_trust_score(story, face_score, doc_score, emotion_score, engagement_score, admin_adjustment):
#     story_score = min(len(story) / 20, 25)  # Max story weight is 25
#     trust_score = round(
#         0.2 * face_score +
#         0.2 * doc_score +
#         0.15 * emotion_score +
#         0.25 * story_score +
#         0.1 * engagement_score +
#         0.1 * admin_adjustment,
#         2
#     )
#     return trust_score

# # -----------------------
# # Routes
# # -----------------------
# @app.route('/')
# def home():
#     return jsonify(message="✅ Trust Score API running. Use /submit (POST) and /records (GET).")

# @app.route('/submit', methods=['POST'])
# def submit():
#     try:
#         # -----------------------
#         # Extract Form Data
#         # -----------------------
#         name = request.form.get('name')
#         story = request.form.get('story')
#         doc_type = request.form.get('supporting_doc_type')
#         aadhaar_number = request.form.get('aadhaar_number')
#         pan_number = request.form.get('pan_number')
#         user_id = request.form.get('user_id')

#         id_img = request.files.get('id_image')
#         selfie_img = request.files.get('selfie_image')
#         supporting_doc = request.files.get('supporting_doc')
#         aadhaar_doc = request.files.get('aadhaar_doc')
#         pan_doc = request.files.get('pan_doc')

#         # -----------------------
#         # Check for Missing Fields
#         # -----------------------
#         if not all([name, story, doc_type, id_img, selfie_img, supporting_doc, aadhaar_number, pan_number, user_id, aadhaar_doc, pan_doc]):
#             return jsonify(error="Missing required fields or files"), 400

#         # -----------------------
#         # Save Uploaded Files
#         # -----------------------
#         upload_dir = "temp"
#         os.makedirs(upload_dir, exist_ok=True)

#         id_path = os.path.join(upload_dir, f"{name}_id.jpg")
#         selfie_path = os.path.join(upload_dir, f"{name}_selfie.jpg")
#         doc_path = os.path.join(upload_dir, f"{name}_{doc_type}.pdf")
#         aadhaar_path = os.path.join(upload_dir, f"{name}_aadhaar.jpg")
#         pan_path = os.path.join(upload_dir, f"{name}_pan.jpg")

#         id_img.save(id_path)
#         selfie_img.save(selfie_path)
#         supporting_doc.save(doc_path)
#         aadhaar_doc.save(aadhaar_path)
#         pan_doc.save(pan_path)

#         logger.info("✔️ All images and documents saved.")

#         # -----------------------
#         # Run Verification Modules
#         # -----------------------
#         face_result = verify_face(
#             id_path, selfie_path,
#             aadhaar_number, pan_number,
#             aadhaar_file_path=aadhaar_path,
#             pan_file_path=pan_path
#         )

#         face_score = face_result.get("total_score", 0)
#         face_match = face_score >= 5  # You may adjust threshold

#         doc_score = verify_supporting_document(doc_path, doc_type)
#         document_verified = doc_score >= 10

#         # -----------------------
#         # Placeholder Scores (can be replaced later)
#         # -----------------------
#         emotion_score = 8.0
#         engagement_score = 7.5
#         admin_adjustment = 0.0

#         # -----------------------
#         # Final Trust Score
#         # -----------------------
#         trust_score = calculate_trust_score(
#             story, face_score, doc_score, emotion_score, engagement_score, admin_adjustment
#         )

#         # -----------------------
#         # Save Record to DB
#         # -----------------------
#         record = TrustScoreRecord(
#             user_id=user_id,
#             name=name,
#             story=story,
#             trust_score=trust_score,
#             face_match=face_match,
#             document_verified=document_verified,
#             emotion_score=emotion_score,
#             engagement_score=engagement_score,
#             admin_adjustment=admin_adjustment,
#             id_image_path=id_path,
#             selfie_image_path=selfie_path,
#             supporting_doc_type=doc_type,
#             supporting_doc_path=doc_path,
#             supporting_doc_score=doc_score,
#             aadhaar_number=aadhaar_number,
#             pan_number=pan_number,
#             aadhaar_file_path=aadhaar_path,
#             pan_file_path=pan_path
#         )

#         db.session.add(record)
#         db.session.commit()
#         logger.info(f"✅ Trust score saved for user: {name}")

#         return jsonify({
#             "message": "✅ Trust score generated successfully",
#             "user_id": user_id,
#             "name": name,
#             "trust_score": trust_score,
#             "face_match": face_match,
#             "document_verified": document_verified
#         })

#     except Exception as e:
#         logger.error(f"❌ Error in /submit: {e}")
#         return jsonify(error="An internal error occurred. Please try again later."), 500

# @app.route('/records', methods=['GET'])
# def get_records():
#     try:
#         records = TrustScoreRecord.query.all()
#         result = []
#         for r in records:
#             result.append({
#                 "id": r.id,
#                 "user_id": r.user_id,
#                 "name": r.name,
#                 "story": r.story,
#                 "trust_score": r.trust_score,
#                 "face_match": r.face_match,
#                 "document_verified": r.document_verified,
#                 "emotion_score": r.emotion_score,
#                 "engagement_score": r.engagement_score,
#                 "admin_adjustment": r.admin_adjustment,
#                 "id_image_path": r.id_image_path,
#                 "selfie_image_path": r.selfie_image_path,
#                 "aadhaar_number": r.aadhaar_number,
#                 "pan_number": r.pan_number,
#                 "aadhaar_file_path": r.aadhaar_file_path,
#                 "pan_file_path": r.pan_file_path,
#                 "supporting_doc_type": r.supporting_doc_type,
#                 "supporting_doc_path": r.supporting_doc_path,
#                 "supporting_doc_score": r.supporting_doc_score,
#                 "created_at": r.created_at.strftime('%Y-%m-%d %H:%M:%S')
#             })
#         return jsonify(records=result)
#     except Exception as e:
#         logger.error(f"❌ Error fetching records: {e}")
#         return jsonify(error="Failed to fetch records."), 500

# # -----------------------
# # Run the App
# # -----------------------
# if __name__ == '__main__':
#     with app.app_context():
#         db.create_all()
#     logger.info("🚀 Trust Score API is running at http://127.0.0.1:5000")
#     app.run(debug=True)

# # from flask import Flask, request, jsonify
# # from flask_sqlalchemy import SQLAlchemy
# # import os
# # import logging

# # # Import verification functions
# # from verifier.face_verifier import verify_face
# # from verifier.ocr_verifier import verify_supporting_document
# # from models import db, TrustScoreRecord

# # # -----------------------
# # # Logging Setup
# # # -----------------------
# # logging.basicConfig(level=logging.INFO)
# # logger = logging.getLogger(__name__)

# # # -----------------------
# # # App & DB Setup
# # # -----------------------
# # app = Flask(__name__)
# # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trustscores.db'
# # app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# # db.init_app(app)

# # # -----------------------
# # # Trust Score Calculation
# # # -----------------------
# # def calculate_trust_score(story, face_score, doc_score, emotion_score, engagement_score, admin_adjustment):
# #     story_score = min(len(story) / 20, 25)  # Max story weight is 25
# #     trust_score = round(
# #         0.2 * face_score +
# #         0.2 * doc_score +
# #         0.15 * emotion_score +
# #         0.25 * story_score +
# #         0.1 * engagement_score +
# #         0.1 * admin_adjustment,
# #         2
# #     )
# #     return trust_score

# # # -----------------------
# # # Routes
# # # -----------------------
# # @app.route('/')
# # def home():
# #     return jsonify(message="✅ Trust Score API running. Use /submit (POST) and /records (GET).")

# # @app.route('/submit', methods=['POST'])
# # def submit():
# #     try:
# #         # -----------------------
# #         # Extract Form Data
# #         # -----------------------
# #         name = request.form.get('name')
# #         story = request.form.get('story')
# #         doc_type = request.form.get('supporting_doc_type')
# #         aadhaar_number = request.form.get('aadhaar_number')
# #         pan_number = request.form.get('pan_number')
# #         user_id = request.form.get('user_id')

# #         id_img = request.files.get('id_image')
# #         selfie_img = request.files.get('selfie_image')
# #         supporting_doc = request.files.get('supporting_doc')

# #         # -----------------------
# #         # Check for Missing Fields
# #         # -----------------------
# #         if not all([name, story, doc_type, id_img, selfie_img, supporting_doc, aadhaar_number, pan_number, user_id]):
# #             return jsonify(error="Missing required fields or files"), 400

# #         # -----------------------
# #         # Save Uploaded Files
# #         # -----------------------
# #         upload_dir = "temp"
# #         os.makedirs(upload_dir, exist_ok=True)

# #         id_path = os.path.join(upload_dir, f"{name}_id.jpg")
# #         selfie_path = os.path.join(upload_dir, f"{name}_selfie.jpg")
# #         doc_path = os.path.join(upload_dir, f"{name}_{doc_type}.pdf")

# #         id_img.save(id_path)
# #         selfie_img.save(selfie_path)
# #         supporting_doc.save(doc_path)

# #         logger.info("✔️ Images and documents saved.")

# #         # -----------------------
# #         # Run Verification Modules
# #         # -----------------------
# #         face_result = verify_face(id_path, selfie_path, aadhaar_number, pan_number)

# #         face_score = face_result.get("total_score", 0)
# #         face_match = face_score >= 5  # You may adjust threshold

# #         doc_score = verify_supporting_document(doc_path, doc_type)
# #         document_verified = doc_score >= 10

# #         # -----------------------
# #         # Placeholder Scores (can be replaced later)
# #         # -----------------------
# #         emotion_score = 8.0
# #         engagement_score = 7.5
# #         admin_adjustment = 0.0

# #         # -----------------------
# #         # Final Trust Score
# #         # -----------------------
# #         trust_score = calculate_trust_score(
# #             story, face_score, doc_score, emotion_score, engagement_score, admin_adjustment
# #         )

# #         # -----------------------
# #         # Save Record to DB
# #         # -----------------------
# #         record = TrustScoreRecord(
# #             user_id=user_id,
# #             name=name,
# #             story=story,
# #             trust_score=trust_score,
# #             face_match=face_match,
# #             document_verified=document_verified,
# #             emotion_score=emotion_score,
# #             engagement_score=engagement_score,
# #             admin_adjustment=admin_adjustment,
# #             id_image_path=id_path,
# #             selfie_image_path=selfie_path,
# #             supporting_doc_type=doc_type,
# #             supporting_doc_path=doc_path,
# #             supporting_doc_score=doc_score,
# #             aadhaar_number=aadhaar_number,
# #             pan_number=pan_number
# #         )

# #         db.session.add(record)
# #         db.session.commit()
# #         logger.info(f"✅ Trust score saved for user: {name}")

# #         return jsonify({
# #             "message": "✅ Trust score generated successfully",
# #             "user_id": user_id,
# #             "name": name,
# #             "trust_score": trust_score,
# #             "face_match": face_match,
# #             "document_verified": document_verified
# #         })

# #     except Exception as e:
# #         logger.error(f"❌ Error in /submit: {e}")
# #         return jsonify(error="An internal error occurred. Please try again later."), 500

# # @app.route('/records', methods=['GET'])
# # def get_records():
# #     try:
# #         records = TrustScoreRecord.query.all()
# #         result = []
# #         for r in records:
# #             result.append({
# #                 "id": r.id,
# #                 "user_id": r.user_id,
# #                 "name": r.name,
# #                 "story": r.story,
# #                 "trust_score": r.trust_score,
# #                 "face_match": r.face_match,
# #                 "document_verified": r.document_verified,
# #                 "emotion_score": r.emotion_score,
# #                 "engagement_score": r.engagement_score,
# #                 "admin_adjustment": r.admin_adjustment,
# #                 "id_image_path": r.id_image_path,
# #                 "selfie_image_path": r.selfie_image_path,
# #                 "aadhaar_number": r.aadhaar_number,
# #                 "pan_number": r.pan_number,
# #                 "supporting_doc_type": r.supporting_doc_type,
# #                 "supporting_doc_path": r.supporting_doc_path,
# #                 "supporting_doc_score": r.supporting_doc_score,
# #                 "created_at": r.created_at.strftime('%Y-%m-%d %H:%M:%S')
# #             })
# #         return jsonify(records=result)
# #     except Exception as e:
# #         logger.error(f"❌ Error fetching records: {e}")
# #         return jsonify(error="Failed to fetch records."), 500

# # # -----------------------
# # # Run the App
# # # -----------------------
# # if __name__ == '__main__':
# #     with app.app_context():
# #         db.create_all()
# #     logger.info("🚀 Trust Score API is running at http://127.0.0.1:5000")
# #     app.run(debug=True)

# # from flask import Flask, request, jsonify
# # from flask_sqlalchemy import SQLAlchemy
# # from datetime import datetime
# # import os
# # import logging

# # # Import verification functions
# # from verifier.face_verifier import verify_face
# # from verifier.ocr_verifier import verify_supporting_document

# # # -----------------------
# # # Logging Setup
# # # -----------------------
# # logging.basicConfig(level=logging.INFO)
# # logger = logging.getLogger(__name__)

# # # -----------------------
# # # App & DB Setup
# # # -----------------------
# # app = Flask(__name__)
# # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trustscores.db'
# # app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# # db = SQLAlchemy(app)

# # # -----------------------
# # # Models
# # # -----------------------
# # class TrustScoreRecord(db.Model):
# #     id = db.Column(db.Integer, primary_key=True)
# #     name = db.Column(db.String(120), nullable=False)
# #     story = db.Column(db.Text, nullable=False)
# #     trust_score = db.Column(db.Float, nullable=False)
# #     face_match = db.Column(db.Boolean, default=False)
# #     document_verified = db.Column(db.Boolean, default=False)
# #     emotion_score = db.Column(db.Float, default=0.0)
# #     engagement_score = db.Column(db.Float, default=0.0)
# #     admin_adjustment = db.Column(db.Float, default=0.0)
# #     id_image_path = db.Column(db.String(255))
# #     selfie_image_path = db.Column(db.String(255))
# #     supporting_doc_type = db.Column(db.String(50))
# #     supporting_doc_path = db.Column(db.String(255))
# #     supporting_doc_score = db.Column(db.Integer, default=0)
# #     created_at = db.Column(db.DateTime, default=datetime.utcnow)

# # # -----------------------
# # # Trust Score Calculation
# # # -----------------------
# # def calculate_trust_score(story, face_score, doc_score, emotion_score, engagement_score, admin_adjustment):
# #     story_score = min(len(story) / 20, 25)  # Max 25
# #     trust_score = round(
# #         0.2 * face_score +
# #         0.2 * doc_score +
# #         0.15 * emotion_score +
# #         0.25 * story_score +
# #         0.1 * engagement_score +
# #         0.1 * admin_adjustment,
# #         2
# #     )
# #     return trust_score

# # # -----------------------
# # # Routes
# # # -----------------------
# # @app.route('/')
# # def home():
# #     return jsonify(message="✅ Trust Score API running. Use /submit (POST) and /records (GET).")

# # @app.route('/submit', methods=['POST'])
# # def submit():
# #     try:
# #         name = request.form.get('name')
# #         story = request.form.get('story')
# #         doc_type = request.form.get('supporting_doc_type')

# #         id_img = request.files.get('id_image')
# #         selfie_img = request.files.get('selfie_image')
# #         supporting_doc = request.files.get('supporting_doc')

# #         if not all([name, story, doc_type, id_img, selfie_img, supporting_doc]):
# #             return jsonify(error="Missing required fields or files"), 400

# #         # Save uploads
# #         upload_dir = "temp"
# #         os.makedirs(upload_dir, exist_ok=True)

# #         id_path = os.path.join(upload_dir, f"{name}_id.jpg")
# #         selfie_path = os.path.join(upload_dir, f"{name}_selfie.jpg")
# #         doc_path = os.path.join(upload_dir, f"{name}_{doc_type}.pdf")

# #         id_img.save(id_path)
# #         selfie_img.save(selfie_path)
# #         supporting_doc.save(doc_path)

# #         logger.info("Images and document saved. Starting verification...")

# #         # Verifications
# #         face_score = verify_face(id_path, selfie_path)
# #         face_match = face_score >= 5

# #         doc_score = verify_supporting_document(doc_path, doc_type)
# #         document_verified = doc_score >= 10

# #         emotion_score = 8.0  # Placeholder
# #         engagement_score = 7.5  # Placeholder
# #         admin_adjustment = 0.0  # Placeholder

# #         trust_score = calculate_trust_score(
# #             story, face_score, doc_score, emotion_score, engagement_score, admin_adjustment
# #         )

# #         record = TrustScoreRecord(
# #             name=name,
# #             story=story,
# #             trust_score=trust_score,
# #             face_match=face_match,
# #             document_verified=document_verified,
# #             emotion_score=emotion_score,
# #             engagement_score=engagement_score,
# #             admin_adjustment=admin_adjustment,
# #             id_image_path=id_path,
# #             selfie_image_path=selfie_path,
# #             supporting_doc_type=doc_type,
# #             supporting_doc_path=doc_path,
# #             supporting_doc_score=doc_score
# #         )

# #         db.session.add(record)
# #         db.session.commit()

# #         return jsonify(
# #             message="✅ Trust score generated successfully",
# #             name=name,
# #             trust_score=trust_score,
# #             document_verified=document_verified
# #         )

# #     except Exception as e:
# #         logger.error(f"❌ Error processing submission: {e}")
# #         return jsonify(error=str(e)), 500

# # @app.route('/records', methods=['GET'])
# # def get_records():
# #     records = TrustScoreRecord.query.all()
# #     result = []
# #     for r in records:
# #         result.append({
# #             "id": r.id,
# #             "name": r.name,
# #             "story": r.story,
# #             "trust_score": r.trust_score,
# #             "face_match": r.face_match,
# #             "document_verified": r.document_verified,
# #             "emotion_score": r.emotion_score,
# #             "engagement_score": r.engagement_score,
# #             "admin_adjustment": r.admin_adjustment,
# #             "id_image_path": r.id_image_path,
# #             "selfie_image_path": r.selfie_image_path,
# #             "supporting_doc_type": r.supporting_doc_type,
# #             "supporting_doc_path": r.supporting_doc_path,
# #             "supporting_doc_score": r.supporting_doc_score,
# #             "created_at": r.created_at.strftime('%Y-%m-%d %H:%M:%S')
# #         })
# #     return jsonify(records=result)

# # # -----------------------
# # # Run App
# # # -----------------------
# # if __name__ == '__main__':
# #     with app.app_context():
# #         db.create_all()
# #     logger.info("Trust Score API is running on http://127.0.0.1:5000")
# #     app.run(debug=True)
