from flask import Blueprint, request, jsonify
from app import db
from app.models import Asset, AssetImpactAssessment, ImpactCriterion
from app.api.asset_routes import update_dependent_assets, recalculate_asset_dependencies
import json

bp = Blueprint('asset_value_bp', __name__, url_prefix='/api/asset-values')

@bp.route('/calculate', methods=['POST'])
def calculate_asset_value():
    """
    Основной маршрут для расчета ценности активов по практике 2
    """
    data = request.get_json()
    
    asset_id = data.get('asset_id')
    asset = Asset.query.get_or_404(asset_id)
    
    # Обновляем свойства ИБ актива
    properties = data.get('properties', {})
    asset.properties = json.dumps(properties)
    
    # Обновляем критерии воздействия
    impacts = data.get('impacts', {})
    asset.business_process_impact = impacts.get('business_process_impact')
    asset.legal_requirements_impact = impacts.get('legal_requirements_impact')
    asset.financial_losses_impact = impacts.get('financial_losses_impact')
    asset.reputation_impact = impacts.get('reputation_impact')
    
    # Обновляем стоимость актива
    asset_cost = data.get('asset_cost')
    if asset_cost:
        asset.asset_cost = float(asset_cost)
        # Автоматическая оценка стоимости по шкале
        if asset_cost <= 20:
            asset.asset_cost_rating = 'низкая'
        elif asset_cost <= 100:
            asset.asset_cost_rating = 'средняя'
        else:
            asset.asset_cost_rating = 'высокая'
    
    # Обновляем зависимости
    old_dependency_value = asset.dependency_value
    dependency_value = data.get('dependency_value')
    if dependency_value:
        # Обновляем dependency_value только если новое значение выше текущего
        if asset.dependency_value is None:
            asset.dependency_value = dependency_value
        else:
            # Сравниваем значения: низкая < средняя < высокая
            priority_map = {'низкая': 1, 'средняя': 2, 'высокая': 3}
            current_priority = priority_map.get(asset.dependency_value, 0)
            new_priority = priority_map.get(dependency_value, 0)
            if new_priority >= current_priority:  # Устанавливаем новое значение, если оно не ниже текущего
                asset.dependency_value = dependency_value
    
    # Определяем итоговую ценность как максимальную из всех критериев
    values = [asset.business_process_impact, asset.legal_requirements_impact,
              asset.financial_losses_impact, asset.reputation_impact]
    values = [v for v in values if v]
    if values:
        # Если есть высокая ценность, то итоговая высокая, иначе средняя, иначе низкая
        if 'В' in values:
            asset.final_value = 'В'
        elif 'С' in values:
            asset.final_value = 'С'
        else:
            asset.final_value = 'Н'
    
    db.session.commit()
    
    # Пересчитываем зависимости для этого актива (учитываем активы, от которых он зависит)
    recalculate_asset_dependencies(asset.id)
    
    # Если dependency_value изменилось, обновляем зависимые активы
    if old_dependency_value != asset.dependency_value and asset.dependency_value is not None:
        update_dependent_assets(asset.id, asset.dependency_value, set())
        db.session.commit()
    
    return jsonify({
        'success': True,
        'asset': asset.to_dict()
    })

@bp.route('/security-properties/<int:asset_id>', methods=['POST'])
def set_security_properties(asset_id):
    """
    Установка свойств информационной безопасности для актива
    """
    asset = Asset.query.get_or_404(asset_id)
    data = request.get_json()
    
    # Преобразуем значения "+" и "-" в булевы значения
    properties = {
        'confidentiality': data.get('confidentiality') == '+',
        'integrity': data.get('integrity') == '+',
        'availability': data.get('availability') == '+'
    }
    
    asset.properties = json.dumps(properties)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'asset': asset.to_dict()
    })

@bp.route('/impact-assessment/<int:asset_id>', methods=['POST'])
def set_impact_assessment(asset_id):
    """
    Установка оценки воздействия по критериям для актива
    """
    asset = Asset.query.get_or_404(asset_id)
    data = request.get_json()
    
    # Получаем или создаем критерии воздействия
    criteria_data = data.get('criteria', [])
    
    for criterion_data in criteria_data:
        criterion_id = criterion_data.get('criterion_id')
        confidentiality_impact = criterion_data.get('confidentiality_impact') or '-'
        integrity_impact = criterion_data.get('integrity_impact') or '-'
        availability_impact = criterion_data.get('availability_impact') or '-'
        
        # Определяем максимальное воздействие
        impacts = [confidentiality_impact, integrity_impact, availability_impact]
        impacts = [i for i in impacts if i and i != '-']
        max_impact = None
        if impacts:
            if 'В' in impacts:
                max_impact = 'В'
            elif 'С' in impacts:
                max_impact = 'С'
            else:
                max_impact = 'Н'
        
        # Проверяем существующую оценку
        assessment = AssetImpactAssessment.query.filter_by(
            asset_id=asset_id,
            impact_criterion_id=criterion_id
        ).first()
        
        if assessment:
            assessment.confidentiality_impact = confidentiality_impact
            assessment.integrity_impact = integrity_impact
            assessment.availability_impact = availability_impact
            assessment.max_impact = max_impact
        else:
            assessment = AssetImpactAssessment(
                asset_id=asset_id,
                impact_criterion_id=criterion_id,
                confidentiality_impact=confidentiality_impact,
                integrity_impact=integrity_impact,
                availability_impact=availability_impact,
                max_impact=max_impact
            )
            db.session.add(assessment)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'asset_id': asset_id
    })

@bp.route('/asset-cost/<int:asset_id>', methods=['POST'])
def set_asset_cost(asset_id):
    """
    Установка стоимости актива и автоматическая оценка
    """
    asset = Asset.query.get_or_404(asset_id)
    data = request.get_json()
    
    cost = data.get('cost')
    if cost:
        asset.asset_cost = float(cost)
        
        # Оценка по шкале стоимости
        if asset.asset_cost <= 20:
            asset.asset_cost_rating = 'низкая'
        elif asset.asset_cost <= 100:
            asset.asset_cost_rating = 'средняя'
        else:
            asset.asset_cost_rating = 'высокая'
        
        db.session.commit()
    
    return jsonify({
        'success': True,
        'asset': asset.to_dict()
    })

@bp.route('/final-value/<int:asset_id>', methods=['POST'])
def calculate_final_value(asset_id):
    """
    Расчет итоговой ценности актива с учетом всех факторов
    """
    asset = Asset.query.get_or_404(asset_id)
    data = request.get_json()
    
    # Получаем ценность без учета зависимостей
    # Не изменяем это значение при оценке зависимостей, только если оно явно передано и не было установлено ранее
    value_without_deps = data.get('value_without_dependencies')
    if value_without_deps is not None and asset.value_without_dependencies is None:
        # Только устанавливаем, если еще не было установлено
        asset.value_without_dependencies = value_without_deps
    
    # Получаем оценку стоимости
    cost_rating = data.get('cost_rating')
    
    # Определяем итоговую ценность
    if value_without_deps == 'В' or cost_rating == 'В':
        asset.final_value = 'В'
    elif value_without_deps == 'С' or cost_rating == 'С':
        asset.final_value = 'С'
    else:
        asset.final_value = 'Н'
    
    # Учитываем зависимости
    dependency_value = data.get('dependency_value')
    old_dependency_value = asset.dependency_value
    
    # Устанавливаем dependency_value напрямую (может быть None если нет зависимостей)
    asset.dependency_value = dependency_value
    
    # Итоговая ценность может быть повышена из-за зависимостей
    if dependency_value == 'высокая' and asset.final_value != 'В':
        asset.final_value = 'В'
    elif dependency_value == 'средняя' and asset.final_value == 'Н':
        asset.final_value = 'С'
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'asset': asset.to_dict()
    })