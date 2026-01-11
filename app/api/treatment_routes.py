from flask import Blueprint, request, jsonify
from app import db
from app.models import RiskTreatmentPlan
from datetime import datetime

bp = Blueprint('treatment_bp', __name__, url_prefix='/api/treatment_plans')

@bp.route('/', methods=['GET'])
def get_treatment_plans():
    plans = RiskTreatmentPlan.query.all()
    return jsonify([plan.to_dict() for plan in plans])

@bp.route('/<int:plan_id>', methods=['GET'])
def get_treatment_plan(plan_id):
    plan = RiskTreatmentPlan.query.get_or_404(plan_id)
    return jsonify(plan.to_dict())

@bp.route('/', methods=['POST'])
def create_treatment_plan():
    data = request.get_json()
    
    plan = RiskTreatmentPlan(
        incident_id=data.get('incident_id'),
        risk_treatment_measures=data.get('risk_treatment_measures'),
        residual_risk=data.get('residual_risk'),
        resources=data.get('resources'),
        deadlines=data.get('deadlines'),
        responsible_persons=data.get('responsible_persons'),
        actions=data.get('actions')
    )
    
    db.session.add(plan)
    db.session.commit()
    
    return jsonify(plan.to_dict()), 201

@bp.route('/<int:plan_id>', methods=['PUT'])
def update_treatment_plan(plan_id):
    plan = RiskTreatmentPlan.query.get_or_404(plan_id)
    data = request.get_json()
    
    plan.incident_id = data.get('incident_id', plan.incident_id)
    plan.risk_treatment_measures = data.get('risk_treatment_measures', plan.risk_treatment_measures)
    plan.residual_risk = data.get('residual_risk', plan.residual_risk)
    plan.resources = data.get('resources', plan.resources)
    plan.deadlines = data.get('deadlines', plan.deadlines)
    plan.responsible_persons = data.get('responsible_persons', plan.responsible_persons)
    plan.actions = data.get('actions', plan.actions)
    plan.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify(plan.to_dict())

@bp.route('/<int:plan_id>', methods=['DELETE'])
def delete_treatment_plan(plan_id):
    plan = RiskTreatmentPlan.query.get_or_404(plan_id)
    
    db.session.delete(plan)
    db.session.commit()
    
    return '', 204