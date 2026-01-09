from app import db

class AssetDependency(db.Model):
    __tablename__ = 'asset_dependencies'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    depends_on_asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    relationship_type = db.Column(db.Text, default='+')  # '+' - есть зависимость, '-' - нет зависимости
    
    __table_args__ = (db.UniqueConstraint('asset_id', 'depends_on_asset_id'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'asset_id': self.asset_id,
            'depends_on_asset_id': self.depends_on_asset_id,
            'relationship_type': self.relationship_type
        }