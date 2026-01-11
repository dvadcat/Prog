from flask import Blueprint, request, jsonify
from app import db
from app.models import DamageScale, ImpactCriterion

bp = Blueprint('damage_scale_bp', __name__, url_prefix='/api/damage-scales')

@bp.route('/', methods=['GET'])
def get_damage_scales():
    """Получить все шкалы оценки ущерба"""
    criterion_id = request.args.get('criterion_id')
    query = DamageScale.query
    
    if criterion_id:
        query = query.filter_by(impact_criterion_id=criterion_id)
    
    scales = query.all()
    return jsonify([scale.to_dict() for scale in scales])

@bp.route('/', methods=['POST'])
def create_damage_scale():
    """Создать новую шкалу оценки ущерба"""
    data = request.get_json()
    
    scale = DamageScale(
        impact_criterion_id=data.get('impact_criterion_id'),
        scale_type=data.get('scale_type'),
        description=data.get('description')
    )
    
    db.session.add(scale)
    db.session.commit()
    
    return jsonify(scale.to_dict()), 201

@bp.route('/<int:scale_id>', methods=['PUT'])
def update_damage_scale(scale_id):
    """Обновить шкалу оценки ущерба"""
    scale = DamageScale.query.get_or_404(scale_id)
    data = request.get_json()
    
    scale.scale_type = data.get('scale_type', scale.scale_type)
    scale.description = data.get('description', scale.description)
    
    db.session.commit()
    return jsonify(scale.to_dict())

@bp.route('/<int:scale_id>', methods=['DELETE'])
def delete_damage_scale(scale_id):
    """Удалить шкалу оценки ущерба"""
    scale = DamageScale.query.get_or_404(scale_id)
    db.session.delete(scale)
    db.session.commit()
    return '', 204

@bp.route('/criterion/<int:criterion_id>', methods=['GET'])
def get_scales_by_criterion(criterion_id):
    """Получить шкалы для конкретного критерия"""
    scales = DamageScale.query.filter_by(impact_criterion_id=criterion_id).all()
    return jsonify([scale.to_dict() for scale in scales])