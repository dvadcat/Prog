from flask import Blueprint, request, jsonify
from app import db
from app.models import Context, Asset
from datetime import datetime

bp = Blueprint('context_bp', __name__, url_prefix='/api/contexts')

@bp.route('/', methods=['GET'])
def get_contexts():
    contexts = Context.query.all()
    return jsonify([context.to_dict() for context in contexts])

@bp.route('/<int:context_id>', methods=['GET'])
def get_context(context_id):
    context = Context.query.get_or_404(context_id)
    return jsonify(context.to_dict())

@bp.route('/', methods=['POST'])
def create_context():
    data = request.get_json()
    
    context = Context(
        name=data.get('name'),
        description=data.get('description'),
        type=data.get('type'),
        owner_name=data.get('owner_name'),
        evaluation_criteria=data.get('evaluation_criteria'),
        risk_evaluation_criteria=data.get('risk_evaluation_criteria'),
        selected_impact_criteria=data.get('selected_impact_criteria'),
        damage_scales=data.get('damage_scales'),
        asset_cost_scale=data.get('asset_cost_scale'),
        risk_acceptance_criteria=data.get('risk_acceptance_criteria')
    )
    
    db.session.add(context)
    db.session.commit()
    
    return jsonify(context.to_dict()), 201

@bp.route('/<int:context_id>', methods=['PUT'])
def update_context(context_id):
    context = Context.query.get_or_404(context_id)
    data = request.get_json()
    
    context.name = data.get('name', context.name)
    context.description = data.get('description', context.description)
    context.type = data.get('type', context.type)
    context.owner_name = data.get('owner_name', context.owner_name)
    context.evaluation_criteria = data.get('evaluation_criteria', context.evaluation_criteria)
    context.risk_evaluation_criteria = data.get('risk_evaluation_criteria', context.risk_evaluation_criteria)
    context.selected_impact_criteria = data.get('selected_impact_criteria', context.selected_impact_criteria)
    context.damage_scales = data.get('damage_scales', context.damage_scales)
    context.asset_cost_scale = data.get('asset_cost_scale', context.asset_cost_scale)
    context.risk_acceptance_criteria = data.get('risk_acceptance_criteria', context.risk_acceptance_criteria)
    context.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify(context.to_dict())

@bp.route('/<int:context_id>', methods=['DELETE'])
def delete_context(context_id):
    context = Context.query.get_or_404(context_id)
    
    # Удаление связанных активов
    assets = Asset.query.filter_by(context_id=context_id).all()
    for asset in assets:
        db.session.delete(asset)
    
    db.session.delete(context)
    db.session.commit()
    
    return '', 204