# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class TrustScoreRecord(db.Model):
    __tablename__ = 'trust_score_records'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    story = db.Column(db.Text, nullable=False)
    trust_score = db.Column(db.Float, nullable=False)

    # Verification Details
    face_match = db.Column(db.Boolean, default=False)
    document_verified = db.Column(db.Boolean, default=False)
    emotion_score = db.Column(db.Float, default=0.0)
    engagement_score = db.Column(db.Float, default=0.0)
    admin_adjustment = db.Column(db.Float, default=0.0)

    # Image Paths
    id_image_path = db.Column(db.String(255))
    selfie_image_path = db.Column(db.String(255))

    # Aadhaar and PAN Numbers
    aadhaar_number = db.Column(db.String(20))
    pan_number = db.Column(db.String(20))

    # Aadhaar and PAN File Paths
    aadhaar_file_path = db.Column(db.String(255))
    pan_file_path = db.Column(db.String(255))

    # Supporting Document Fields
    supporting_doc_type = db.Column(db.String(50))
    supporting_doc_path = db.Column(db.String(255))
    supporting_doc_score = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<TrustScoreRecord {self.user_id} - Score: {self.trust_score}>"

# from flask_sqlalchemy import SQLAlchemy
# from datetime import datetime

# db = SQLAlchemy()

# class TrustScoreRecord(db.Model):
#     __tablename__ = 'trust_score_records'

#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.String(50), nullable=False)  # Removed ForeignKey
#     name = db.Column(db.String(100), nullable=False)
#     story = db.Column(db.Text, nullable=False)
#     trust_score = db.Column(db.Float, nullable=False)

#     # Verification Details
#     face_match = db.Column(db.Boolean, default=False)
#     document_verified = db.Column(db.Boolean, default=False)
#     emotion_score = db.Column(db.Float, default=0.0)
#     engagement_score = db.Column(db.Float, default=0.0)
#     admin_adjustment = db.Column(db.Float, default=0.0)

#     # Image Paths
#     id_image_path = db.Column(db.String(255))
#     selfie_image_path = db.Column(db.String(255))

#     # Aadhaar and PAN
#     aadhaar_number = db.Column(db.String(20))
#     pan_number = db.Column(db.String(20))

#     aadhaar_file_path = db.Column(db.String(255))
#     pan_file_path = db.Column(db.String(255))

#     # Supporting Document Fields
#     supporting_doc_type = db.Column(db.String(50))
#     supporting_doc_path = db.Column(db.String(255))
#     supporting_doc_score = db.Column(db.Integer, default=0)

#     created_at = db.Column(db.DateTime, default=datetime.utcnow)

#     def __repr__(self):
#         return f"<TrustScoreRecord {self.user_id} - Score: {self.trust_score}>"
