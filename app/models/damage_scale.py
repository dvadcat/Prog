from app import db

class DamageScale(db.Model):
    __tablename__ = 'damage_scales'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    impact_criterion_id = db.Column(db.Integer, db.ForeignKey('impact_criteria.id'), nullable=False)
    scale_type = db.Column(db.Text, nullable=False)  # 'low', 'medium', 'high'
    description = db.Column(db.Text, nullable=False)  # описание шкалы
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Связь с критерием воздействия
    impact_criterion = db.relationship('ImpactCriterion', backref='damage_scales')
    
    def to_dict(self):
        return {
            'id': self.id,
            'impact_criterion_id': self.impact_criterion_id,
            'scale_type': self.scale_type,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }