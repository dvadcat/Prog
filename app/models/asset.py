from app import db
from datetime import datetime
from sqlalchemy import event

class Asset(db.Model):
    __tablename__ = 'assets'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    context_id = db.Column(db.Integer, db.ForeignKey('contexts.id'), nullable=False)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    type = db.Column(db.Text, db.CheckConstraint("type IN ('information', 'software', 'hardware')"), nullable=False)
    properties = db.Column(db.Text)  # JSON {"confidentiality": true, "integrity": true, "availability": true}
    impact_score = db.Column(db.Integer, default=0)  # числовой показатель воздействия
    cost_value = db.Column(db.Text, db.CheckConstraint("cost_value IN ('низкая', 'средняя', 'высокая', 'критическая')"))  # оценка стоимости
    value_without_dependencies = db.Column(db.Text, db.CheckConstraint("value_without_dependencies IN ('-', 'Н', 'С', 'В')"))  # ценность без учета зависимостей
    final_value = db.Column(db.Text, db.CheckConstraint("final_value IN ('-', 'Н', 'С', 'В')"))  # итоговая ценность
    business_process_impact = db.Column(db.Text, db.CheckConstraint("business_process_impact IN ('минимальная', 'средняя', 'высокая')"))
    legal_requirements_impact = db.Column(db.Text, db.CheckConstraint("legal_requirements_impact IN ('минимальная', 'средняя', 'высокая')"))
    financial_losses_impact = db.Column(db.Text, db.CheckConstraint("financial_losses_impact IN ('минимальная', 'средняя', 'высокая')"))
    reputation_impact = db.Column(db.Text, db.CheckConstraint("reputation_impact IN ('минимальная', 'средняя', 'высокая')"))
    asset_cost = db.Column(db.Float)  # стоимость актива в тыс. руб.
    asset_cost_rating = db.Column(db.Text, db.CheckConstraint("asset_cost_rating IN ('низкая', 'средняя', 'высокая')"))  # оценка стоимости актива
    dependency_value = db.Column(db.Text, db.CheckConstraint("dependency_value IN ('низкая', 'средняя', 'высокая')"))  # ценность с учетом зависимостей
    impact_matrix = db.Column(db.Text)  # матрица воздействия (JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связи
    dependencies = db.relationship('AssetDependency', backref='asset', lazy=True, cascade='all, delete-orphan', foreign_keys='AssetDependency.asset_id')
    dependent_on = db.relationship('AssetDependency', backref='depends_on_asset', lazy=True, foreign_keys='AssetDependency.depends_on_asset_id')
    asset_threats = db.relationship('AssetThreat', backref='asset', lazy=True, cascade='all, delete-orphan')
    asset_vulnerabilities = db.relationship('AssetVulnerability', backref='asset', lazy=True, cascade='all, delete-orphan')
    incidents = db.relationship('Incident', backref='asset', lazy=True, cascade='all, delete-orphan')
    impact_assessments = db.relationship('AssetImpactAssessment', backref='asset', lazy=True, cascade='all, delete-orphan')
    threat_assessments = db.relationship('ThreatAssessment', backref='asset', lazy=True, cascade='all, delete-orphan')
    vulnerability_assessments = db.relationship('VulnerabilityAssessment', backref='asset', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'context_id': self.context_id,
            'context': {'name': self.context.name} if self.context else None,
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'properties': self.properties,
            'impact_score': self.impact_score,
            'cost_value': self.cost_value,
            'value_without_dependencies': self.value_without_dependencies,
            'final_value': self.final_value,
            'business_process_impact': self.business_process_impact,
            'legal_requirements_impact': self.legal_requirements_impact,
            'financial_losses_impact': self.financial_losses_impact,
            'reputation_impact': self.reputation_impact,
            'asset_cost': self.asset_cost,
            'asset_cost_rating': self.asset_cost_rating,
            'dependency_value': self.dependency_value,
            'impact_matrix': self.impact_matrix,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Триггер для обновления времени
@event.listens_for(Asset, 'before_update')
def update_asset_timestamp(mapper, connection, target):
    target.updated_at = datetime.utcnow()