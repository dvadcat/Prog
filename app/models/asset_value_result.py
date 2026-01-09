from app import db

class AssetValueResult(db.Model):
    __tablename__ = 'asset_value_results'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    type = db.Column(db.Text, nullable=False) # 'information', 'software', 'hardware'
    value_without_dependencies = db.Column(db.Text)  # ценность без учета зависимостей
    value_with_dependencies = db.Column(db.Text)  # ценность с учетом зависимостей
    final_value = db.Column(db.Text)  # итоговая ценность
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Связь с активом
    asset = db.relationship('Asset', backref='value_results')
    
    def to_dict(self):
        return {
            'id': self.id,
            'asset_id': self.asset_id,
            'type': self.type,
            'value_without_dependencies': self.value_without_dependencies,
            'value_with_dependencies': self.value_with_dependencies,
            'final_value': self.final_value,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }