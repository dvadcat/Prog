from app import db

class ImpactCriterion(db.Model):
    __tablename__ = 'impact_criteria'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, nullable=False, unique=True)  # наименование критерия
    low_desc = db.Column(db.Text)  # описание низкого уровня
    mid_desc = db.Column(db.Text)  # описание среднего уровня
    high_desc = db.Column(db.Text)  # описание высокого уровня
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Связи
    context_impact_criteria = db.relationship('ContextImpactCriterion', backref='impact_criterion', lazy=True, cascade='all, delete-orphan')
    asset_impact_assessments = db.relationship('AssetImpactAssessment', backref='impact_criterion', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'low_desc': self.low_desc,
            'mid_desc': self.mid_desc,
            'high_desc': self.high_desc,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }