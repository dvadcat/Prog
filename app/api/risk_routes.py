from flask import Blueprint, request, jsonify
from app import db
from app.models import Risk
from datetime import datetime

bp = Blueprint('risk_bp', __name__, url_prefix='/api/risks')

@bp.route('/', methods=['GET'])
def get_risks():
    risks = Risk.query.all()
    return jsonify([risk.to_dict() for risk in risks])

@bp.route('/<int:risk_id>', methods=['GET'])
def get_risk(risk_id):
    risk = Risk.query.get_or_404(risk_id)
    return jsonify(risk.to_dict())

@bp.route('/', methods=['POST'])
def create_risk():
    data = request.get_json()
    
    risk = Risk(
        incident_id=data.get('incident_id'),
        likelihood=data.get('likelihood'),
        impact_level=data.get('impact_level'),
        vulnerability_level=data.get('vulnerability_level'),
        scenario_probability=data.get('scenario_probability'),
        risk_score=data.get('risk_score'),
        risk_level=data.get('risk_level'),
        acceptable=data.get('acceptable')
    )
    
    db.session.add(risk)
    db.session.commit()
    
    return jsonify(risk.to_dict()), 201

@bp.route('/<int:risk_id>', methods=['PUT'])
def update_risk(risk_id):
    risk = Risk.query.get_or_404(risk_id)
    data = request.get_json()
    
    risk.incident_id = data.get('incident_id', risk.incident_id)
    risk.likelihood = data.get('likelihood', risk.likelihood)
    risk.impact_level = data.get('impact_level', risk.impact_level)
    risk.vulnerability_level = data.get('vulnerability_level', risk.vulnerability_level)
    risk.scenario_probability = data.get('scenario_probability', risk.scenario_probability)
    risk.risk_score = data.get('risk_score', risk.risk_score)
    risk.risk_level = data.get('risk_level', risk.risk_level)
    risk.acceptable = data.get('acceptable', risk.acceptable)
    risk.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify(risk.to_dict())

@bp.route('/<int:risk_id>', methods=['DELETE'])
def delete_risk(risk_id):
    risk = Risk.query.get_or_404(risk_id)
    
    db.session.delete(risk)
    db.session.commit()
    
    return '', 204