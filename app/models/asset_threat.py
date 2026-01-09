from app import db

class AssetThreat(db.Model):
    __tablename__ = 'asset_threats'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    threat_id = db.Column(db.Integer, db.ForeignKey('threats.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    __table_args__ = (db.UniqueConstraint('asset_id', 'threat_id'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'asset_id': self.asset_id,
            'threat_id': self.threat_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }