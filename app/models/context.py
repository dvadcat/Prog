from app import db
from datetime import datetime
from sqlalchemy import event

class Context(db.Model):
    __tablename__ = 'contexts'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    type = db.Column(db.Text)
    owner_name = db.Column(db.Text)
    evaluation_criteria = db.Column(db.Text) # JSON с критериями оценки и принятия риска (устаревшее поле)
    risk_evaluation_criteria = db.Column(db.Text) # JSON с критериями оценивания рисков ИБ
    selected_impact_criteria = db.Column(db.Text)  # JSON с выбранными критериями влияния рисков
    damage_scales = db.Column(db.Text) # JSON с шкалами ущерба для каждого критерия
    asset_cost_scale = db.Column(db.Text)  # JSON с шкалой стоимости актива
    risk_acceptance_criteria = db.Column(db.Text)  # JSON с критериями принятия риска (приемлемый/неприемлемый)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связи
    assets = db.relationship('Asset', backref='context', lazy=True, cascade='all, delete-orphan')
    context_impact_criteria = db.relationship('ContextImpactCriterion', backref='context', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'owner_name': self.owner_name,
            'evaluation_criteria': self.evaluation_criteria,
            'risk_evaluation_criteria': self.risk_evaluation_criteria,
            'selected_impact_criteria': self.selected_impact_criteria,
            'damage_scales': self.damage_scales,
            'asset_cost_scale': self.asset_cost_scale,
            'risk_acceptance_criteria': self.risk_acceptance_criteria,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ContextImpactCriterion(db.Model):
    __tablename__ = 'context_impact_criteria'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    context_id = db.Column(db.Integer, db.ForeignKey('contexts.id'), nullable=False)
    impact_criterion_id = db.Column(db.Integer, db.ForeignKey('impact_criteria.id'), nullable=False)
    
    __table_args__ = (db.UniqueConstraint('context_id', 'impact_criterion_id'),)

# Триггер для обновления времени
@event.listens_for(Context, 'before_update')
def update_context_timestamp(mapper, connection, target):
    target.updated_at = datetime.utcnow()