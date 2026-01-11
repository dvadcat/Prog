from app import db
from datetime import datetime
from sqlalchemy import event

class Risk(db.Model):
    __tablename__ = 'risks'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    incident_id = db.Column(db.Integer, db.ForeignKey('incidents.id'), nullable=False)
    likelihood = db.Column(db.Text, db.CheckConstraint("likelihood IN ('низкая', 'средняя', 'высокая')")) # вероятность
    impact_level = db.Column(db.Text, db.CheckConstraint("impact_level IN ('низкий', 'средний', 'высокий')"))  # уровень последствий
    vulnerability_level = db.Column(db.Text, db.CheckConstraint("vulnerability_level IN ('Н', 'С', 'В')"))  # уровень уязвимости
    scenario_probability = db.Column(db.Integer)  # числовая оценка вероятности сценария (1-5)
    risk_score = db.Column(db.Integer)  # числовой уровень риска (1-5)
    risk_level = db.Column(db.Text, db.CheckConstraint("risk_level IN ('низкий', 'средний', 'высокий')"))  # качественная оценка уровня риска
    acceptable = db.Column(db.Boolean)  # приемлемость
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'incident_id': self.incident_id,
            'incident': self.incident.to_dict() if self.incident else None,
            'likelihood': self.likelihood,
            'impact_level': self.impact_level,
            'vulnerability_level': self.vulnerability_level,
            'scenario_probability': self.scenario_probability,
            'risk_score': self.risk_score,
            'risk_level': self.risk_level,
            'acceptable': self.acceptable,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Триггер для обновления времени
@event.listens_for(Risk, 'before_update')
def update_risk_timestamp(mapper, connection, target):
    target.updated_at = datetime.utcnow()