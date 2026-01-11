from flask import Blueprint, request, jsonify
from app import db
from app.models import AssetSecurityPropertyImpact, Asset, ImpactCriterion

bp = Blueprint('asset_security_property_impact_bp', __name__, url_prefix='/api/asset-security-property-impacts')

@bp.route('/', methods=['GET'])
def get_asset_security_property_impacts():
    """Получить все оценки воздействия на свойства ИБ"""
    asset_id = request.args.get('asset_id')
    property_name = request.args.get('property')
    criterion_id = request.args.get('criterion_id')
    
    query = AssetSecurityPropertyImpact.query
    
    if asset_id:
        query = query.filter_by(asset_id=asset_id)
    if property_name:
        query = query.filter_by(security_property=property_name)
    if criterion_id:
        query = query.filter_by(impact_criterion_id=criterion_id)
    
    impacts = query.all()
    return jsonify([impact.to_dict() for impact in impacts])

@bp.route('/', methods=['POST'])
def create_asset_security_property_impact():
    """Создать новую оценку воздействия на свойство ИБ"""
    data = request.get_json()
    
    # Проверяем, что такой записи еще нет
    existing = AssetSecurityPropertyImpact.query.filter_by(
        asset_id=data.get('asset_id'),
        security_property=data.get('security_property'),
        impact_criterion_id=data.get('impact_criterion_id')
    ).first()
    
    if existing:
        # Обновляем существующую запись
        existing.impact_value = data.get('impact_value')
        db.session.commit()
        return jsonify(existing.to_dict())
    else:
        # Создаем новую запись
        impact = AssetSecurityPropertyImpact(
            asset_id=data.get('asset_id'),
            security_property=data.get('security_property'),
            impact_criterion_id=data.get('impact_criterion_id'),
            impact_value=data.get('impact_value')
        )
        
        db.session.add(impact)
        db.session.commit()
        
        return jsonify(impact.to_dict()), 201

@bp.route('/<int:impact_id>', methods=['PUT'])
def update_asset_security_property_impact(impact_id):
    """Обновить оценку воздействия на свойство ИБ"""
    impact = AssetSecurityPropertyImpact.query.get_or_404(impact_id)
    data = request.get_json()
    
    impact.impact_value = data.get('impact_value', impact.impact_value)
    
    db.session.commit()
    return jsonify(impact.to_dict())

@bp.route('/<int:impact_id>', methods=['DELETE'])
def delete_asset_security_property_impact(impact_id):
    """Удалить оценку воздействия на свойство ИБ"""
    impact = AssetSecurityPropertyImpact.query.get_or_404(impact_id)
    db.session.delete(impact)
    db.session.commit()
    return '', 204

@bp.route('/asset/<int:asset_id>', methods=['GET'])
def get_impacts_by_asset(asset_id):
    """Получить все оценки воздействия для конкретного актива"""
    impacts = AssetSecurityPropertyImpact.query.filter_by(asset_id=asset_id).all()
    return jsonify([impact.to_dict() for impact in impacts])

@bp.route('/bulk-update', methods=['POST'])
def bulk_update_impacts():
    """Массовое обновление оценок воздействия для актива"""
    data = request.get_json()
    asset_id = data.get('asset_id')
    impacts_data = data.get('impacts', [])
    
    for impact_data in impacts_data:
        # Проверяем, есть ли уже такая запись
        existing = AssetSecurityPropertyImpact.query.filter_by(
            asset_id=asset_id,
            security_property=impact_data.get('security_property'),
            impact_criterion_id=impact_data.get('impact_criterion_id')
        ).first()
        
        if existing:
            existing.impact_value = impact_data.get('impact_value')
        else:
            impact = AssetSecurityPropertyImpact(
                asset_id=asset_id,
                security_property=impact_data.get('security_property'),
                impact_criterion_id=impact_data.get('impact_criterion_id'),
                impact_value=impact_data.get('impact_value')
            )
            db.session.add(impact)
    
    db.session.commit()
    
    impacts = AssetSecurityPropertyImpact.query.filter_by(asset_id=asset_id).all()
    return jsonify([impact.to_dict() for impact in impacts])