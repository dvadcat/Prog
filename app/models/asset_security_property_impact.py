from app import db

class AssetSecurityPropertyImpact(db.Model):
    __tablename__ = 'asset_security_property_impacts'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    security_property = db.Column(db.Text, nullable=False)  # 'confidentiality', 'integrity', 'availability'
    impact_criterion_id = db.Column(db.Integer, db.ForeignKey('impact_criteria.id'), nullable=False)
    impact_value = db.Column(db.Text, db.CheckConstraint("impact_value IN ('Н', 'С', 'В', '-')"))  # Низкий, Средний, Высокий, Нет
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Связи
    asset = db.relationship('Asset', backref='security_property_impacts')
    impact_criterion = db.relationship('ImpactCriterion', backref='asset_property_impacts')
    
    __table_args__ = (db.UniqueConstraint('asset_id', 'security_property', 'impact_criterion_id'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'asset_id': self.asset_id,
            'security_property': self.security_property,
            'impact_criterion_id': self.impact_criterion_id,
            'impact_value': self.impact_value,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }