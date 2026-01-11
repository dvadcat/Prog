from app import db

class ThreatAssessment(db.Model):
    __tablename__ = 'threat_assessment'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    threat_id = db.Column(db.Integer, db.ForeignKey('threats.id'), nullable=False)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    cia_values = db.Column(db.Text)  # значения КДЦ по угрозе
    features_count = db.Column(db.Integer)  # количество признаков
    score = db.Column(db.Float)  # баллы
    assessment = db.Column(db.Text)  # оценка
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    __table_args__ = (db.UniqueConstraint('threat_id', 'asset_id'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'threat_id': self.threat_id,
            'asset_id': self.asset_id,
            'cia_values': self.cia_values,
            'features_count': self.features_count,
            'score': self.score,
            'assessment': self.assessment,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }