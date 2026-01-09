from app import db
from datetime import datetime
import os

class Report(db.Model):
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    context_id = db.Column(db.Integer, db.ForeignKey('contexts.id'), nullable=True)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)
    selected_data = db.Column(db.Text, nullable=True)  # JSON с выбранными данными
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    context = db.relationship('Context', backref=db.backref('reports', lazy=True))
    
    def __repr__(self):
        return f'<Report {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'context_id': self.context_id,
            'context_name': self.context.name if self.context else '',
            'file_path': self.file_path,
            'file_size': self.file_size,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }