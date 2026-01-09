from app import db
from datetime import datetime
from sqlalchemy import event

class Incident(db.Model):
    __tablename__ = 'incidents'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    threat_id = db.Column(db.Integer, db.ForeignKey('threats.id'), nullable=False)
    vulnerability_id = db.Column(db.Text, db.ForeignKey('vulnerabilities.id'), nullable=False)
    operational_impact = db.Column(db.Text)  # JSON ["confidentiality", "integrity", "availability"]
    business_impact = db.Column(db.Text)  # последствия для бизнеса
    impact_level = db.Column(db.Text, db.CheckConstraint("impact_level IN ('низкий', 'средний', 'высокий', 'критический') OR impact_level IS NULL"))
    scenario_name = db.Column(db.Text)  # обозначение сценария инцидента
    scenario_probability = db.Column(db.Integer, db.CheckConstraint("scenario_probability IN (1, 2, 3, 4, 5) OR scenario_probability IS NULL"))  # оценка вероятности сценария инцидента (1-5)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связи
    risks = db.relationship('Risk', backref='incident', lazy=True, cascade='all, delete-orphan')
    treatment_plans = db.relationship('RiskTreatmentPlan', backref='incident', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'asset_id': self.asset_id,
            'asset': self.asset.to_dict() if self.asset else None,
            'threat_id': self.threat_id,
            'threat': self.threat.to_dict() if self.threat else None,
            'vulnerability_id': self.vulnerability_id,
            'vulnerability': self.vulnerability.to_dict() if self.vulnerability else None,
            'operational_impact': self.operational_impact,
            'business_impact': self.business_impact,
            'impact_level': self.impact_level,
            'scenario_name': self.scenario_name,
            'scenario_probability': self.scenario_probability,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Триггер для обновления времени
@event.listens_for(Incident, 'before_update')
def update_incident_timestamp(mapper, connection, target):
    target.updated_at = datetime.utcnow()