from app import db
from datetime import datetime

class Threat(db.Model):
    __tablename__ = 'threats'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bdu_id = db.Column(db.Integer, nullable=True)  # идентификатор УБИ из БДУ ФСТЭК
    name = db.Column(db.Text, nullable=False)  # наименование угрозы
    description = db.Column(db.Text)  # описание
    source = db.Column(db.Text)  # источник угрозы
    target_object = db.Column(db.Text) # объект воздействия
    confidentiality_violation = db.Column(db.Integer, default=0)  # нарушение конфиденциальности (1/0)
    integrity_violation = db.Column(db.Integer, default=0)  # нарушение целостности (1/0)
    availability_violation = db.Column(db.Integer, default=0)  # нарушение доступности (1/0)
    likelihood = db.Column(db.Text, db.CheckConstraint("likelihood IN ('низкая', 'средняя', 'высокая')"))  # вероятность
    is_relevant = db.Column(db.Boolean, default=False)  # актуальность угрозы
    published_at = db.Column(db.Date)
    updated_at = db.Column(db.Date)
    source_assessment = db.Column(db.Text)  # оценка источника угрозы в JSON формате
    probability_assessment = db.Column(db.Text)  # оценка вероятности реализации угрозы в JSON формате
    imported_from_bdu = db.Column(db.Boolean, default=False)  # импортировано из БДУ ФСТЭК
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    step5 = db.Column(db.Text)  # данные о чекбоксах шага 5 в JSON формате
    
    # Связи
    asset_threats = db.relationship('AssetThreat', backref='threat', lazy=True, cascade='all, delete-orphan')
    incidents = db.relationship('Incident', backref='threat', lazy=True, cascade='all, delete-orphan')
    threat_assessments = db.relationship('ThreatAssessment', backref='threat', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'bdu_id': self.bdu_id,
            'name': self.name,
            'description': self.description,
            'source': self.source,
            'target_object': self.target_object,
            'confidentiality_violation': bool(self.confidentiality_violation),
            'integrity_violation': bool(self.integrity_violation),
            'availability_violation': bool(self.availability_violation),
            'likelihood': self.likelihood,
            'is_relevant': self.is_relevant,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'source_assessment': self.source_assessment,
            'probability_assessment': self.probability_assessment,
            'imported_from_bdu': self.imported_from_bdu,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'step5': self.step5
        }