from app import db
from datetime import datetime
from sqlalchemy import event

class RiskTreatmentPlan(db.Model):
    __tablename__ = 'risk_treatment_plans'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    incident_id = db.Column(db.Integer, db.ForeignKey('incidents.id'), nullable=False)
    risk_treatment_measures = db.Column(db.Text, nullable=False)  # меры по обработке риска
    residual_risk = db.Column(db.Text, db.CheckConstraint("residual_risk IN ('низкий', 'средний', 'высокий')"))  # остаточный риск
    resources = db.Column(db.Text)  # необходимые ресурсы
    deadlines = db.Column(db.Text)  # сроки
    responsible_persons = db.Column(db.Text)  # ответственные
    actions = db.Column(db.Text)  # предпринятые действия/статус выполнения
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'incident_id': self.incident_id,
            'risk_treatment_measures': self.risk_treatment_measures,
            'residual_risk': self.residual_risk,
            'resources': self.resources,
            'deadlines': self.deadlines,
            'responsible_persons': self.responsible_persons,
            'actions': self.actions,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Триггер для обновления времени
@event.listens_for(RiskTreatmentPlan, 'before_update')
def update_treatment_plan_timestamp(mapper, connection, target):
    target.updated_at = datetime.utcnow()