from app import db

class AssetImpactAssessment(db.Model):
    __tablename__ = 'asset_impact_assessment'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    impact_criterion_id = db.Column(db.Integer, db.ForeignKey('impact_criteria.id'), nullable=False)
    confidentiality_impact = db.Column(db.Text, db.CheckConstraint("confidentiality_impact IN ('-', 'Н', 'С', 'В')"))
    integrity_impact = db.Column(db.Text, db.CheckConstraint("integrity_impact IN ('-', 'Н', 'С', 'В')"))
    availability_impact = db.Column(db.Text, db.CheckConstraint("availability_impact IN ('-', 'Н', 'С', 'В')"))
    max_impact = db.Column(db.Text, db.CheckConstraint("max_impact IN ('-', 'Н', 'С', 'В')"))  # максимальное значение из трех
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    __table_args__ = (db.UniqueConstraint('asset_id', 'impact_criterion_id'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'asset_id': self.asset_id,
            'impact_criterion_id': self.impact_criterion_id,
            'confidentiality_impact': self.confidentiality_impact,
            'integrity_impact': self.integrity_impact,
            'availability_impact': self.availability_impact,
            'max_impact': self.max_impact,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }