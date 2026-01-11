from flask import Blueprint, request, jsonify
from app import db
from app.models import Asset, AssetDependency, AssetImpactAssessment, AssetSecurityPropertyImpact, ImpactCriterion, ContextImpactCriterion
from datetime import datetime

bp = Blueprint('asset_bp', __name__, url_prefix='/api/assets')

def update_dependent_assets(asset_id, new_dependency_value, visited_assets=None):
    """
    Обновляет dependency_value для всех активов, которые зависят от данного актива
    (только если у них есть зависимости)
    """
    if new_dependency_value is None:
        return
    
    if visited_assets is None:
        visited_assets = set()
    
    # Избегаем циклических зависимостей
    if asset_id in visited_assets:
        return
    visited_assets.add(asset_id)
    
    # Находим все зависимости, где данный актив является "depends_on_asset_id"
    # (т.е. другие активы зависят от него)
    dependencies = AssetDependency.query.filter_by(depends_on_asset_id=asset_id).all()
    
    for dep in dependencies:
        # Получаем актив, который зависит от текущего актива
        dependent_asset = Asset.query.get(dep.asset_id)
        if dependent_asset:
            # Проверяем, есть ли у зависимого актива собственные зависимости
            # (только тогда мы устанавливаем ему dependency_value)
            dependent_asset_dependencies = AssetDependency.query.filter_by(asset_id=dependent_asset.id).all()
            
            if dependent_asset_dependencies:  # Только если у актива есть зависимости
                # Преобразуем значения для сравнения
                dependency_value_map = {'низкая': 1, 'средняя': 2, 'высокая': 3}
                
                current_dep_priority = dependency_value_map.get(dependent_asset.dependency_value, 0) if dependent_asset.dependency_value else 0
                new_dep_priority = dependency_value_map.get(new_dependency_value, 0)
                
                # Обновляем только если новое значение выше текущего
                if new_dep_priority > current_dep_priority:
                    # Обновляем dependency_value
                    dependent_asset.dependency_value = new_dependency_value
                    
                    # НЕ обновляем value_without_dependencies - это независимая характеристика
                    
                    # Обновляем final_value если необходимо
                    if new_dependency_value == 'высокая' and dependent_asset.final_value != 'В':
                        dependent_asset.final_value = 'В'
                    elif new_dependency_value == 'средняя' and dependent_asset.final_value == 'Н':
                        dependent_asset.final_value = 'С'
                    
                    db.session.commit()
                    
                    # Рекурсивно обновляем активы, зависящие от только что обновленного актива
                    update_dependent_assets(dependent_asset.id, new_dependency_value, visited_assets)


def recalculate_asset_dependencies(asset_id):
    """
    Пересчитывает dependency_value для актива на основе максимальной ценности без зависимостей
    всех связанных активов (только если у актива есть зависимости)
    """
    asset = Asset.query.get(asset_id)
    if not asset:
        return
    
    # Находим все зависимости, где данный актив является "asset_id"
    # (т.е. он зависит от других активов)
    dependencies = AssetDependency.query.filter_by(asset_id=asset_id).all()
    
    # Если у актива нет зависимостей, очищаем dependency_value
    if not dependencies:
        if asset.dependency_value is not None:
            asset.dependency_value = None
            db.session.commit()
        return
    
    # Собираем все связанные активы (сам актив + активы, от которых он зависит)
    related_asset_ids = [asset_id]
    for dep in dependencies:
        related_asset_ids.append(dep.depends_on_asset_id)
    
    # Находим максимальную ценность без зависимостей среди всех связанных активов
    max_value_without_deps = None
    priority_map = {'Н': 1, 'С': 2, 'В': 3}
    
    for related_id in related_asset_ids:
        related_asset = Asset.query.get(related_id)
        if related_asset and related_asset.value_without_dependencies:
            asset_priority = priority_map.get(related_asset.value_without_dependencies, 0)
            if max_value_without_deps is None or asset_priority > priority_map.get(max_value_without_deps, 0):
                max_value_without_deps = related_asset.value_without_dependencies
    
    # Если не нашли ценность без зависимостей, используем текущее значение или устанавливаем по умолчанию
    if max_value_without_deps is None:
        max_value_without_deps = asset.value_without_dependencies or 'С'  # По умолчанию средняя
    
    # Преобразуем в формат для dependency_value
    dependency_value_map = {'Н': 'низкая', 'С': 'средняя', 'В': 'высокая'}
    max_dependency_value = dependency_value_map.get(max_value_without_deps, 'средняя')
    
    # Обновляем значение, если оно увеличилось (только повышаем, не понижаем)
    if asset.dependency_value != max_dependency_value and max_dependency_value is not None:
        # Убедимся, что значение только увеличивается, не уменьшается
        priority_map_dep = {'низкая': 1, 'средняя': 2, 'высокая': 3}
        current_priority = priority_map_dep.get(asset.dependency_value, 0) if asset.dependency_value else 0
        new_priority = priority_map_dep.get(max_dependency_value, 0) if max_dependency_value else 0
        
        if new_priority > current_priority:  # Только если новое значение выше
            old_dependency_value = asset.dependency_value
            asset.dependency_value = max_dependency_value
            # НЕ обновляем value_without_dependencies - это независимая характеристика
            db.session.commit()
            
            # Если значение изменилось, обновляем активы, которые зависят от этого актива
            if old_dependency_value != max_dependency_value:
                update_dependent_assets(asset.id, max_dependency_value, set())

@bp.route('/', methods=['GET'])
def get_assets():
    context_id = request.args.get('context_id')
    query = Asset.query
    
    if context_id:
        query = query.filter_by(context_id=context_id)
    
    assets = query.all()
    return jsonify([asset.to_dict() for asset in assets])

@bp.route('/<int:asset_id>', methods=['GET'])
def get_asset(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    return jsonify(asset.to_dict())

@bp.route('/', methods=['POST'])
def create_asset():
    data = request.get_json()
    
    # Обработка полей с CHECK constraint - преобразуем пустые строки в None
    cost_value = data.get('cost_value')
    if cost_value == '':
        cost_value = None
        
    value_without_dependencies = data.get('value_without_dependencies')
    if value_without_dependencies == '':
        value_without_dependencies = None
        
    final_value = data.get('final_value')
    if final_value == '':
        final_value = None
        
    business_process_impact = data.get('business_process_impact')
    if business_process_impact == '':
        business_process_impact = None
        
    legal_requirements_impact = data.get('legal_requirements_impact')
    if legal_requirements_impact == '':
        legal_requirements_impact = None
        
    financial_losses_impact = data.get('financial_losses_impact')
    if financial_losses_impact == '':
        financial_losses_impact = None
        
    reputation_impact = data.get('reputation_impact')
    if reputation_impact == '':
        reputation_impact = None
        
    asset_cost_rating = data.get('asset_cost_rating')
    if asset_cost_rating == '':
        asset_cost_rating = None
        
    dependency_value = data.get('dependency_value')
    if dependency_value == '':
        dependency_value = None

    asset = Asset(
        context_id=data.get('context_id'),
        name=data.get('name'),
        description=data.get('description'),
        type=data.get('type'),
        properties=data.get('properties'),
        impact_score=data.get('impact_score', 0),
        cost_value=cost_value,
        value_without_dependencies=value_without_dependencies,
        final_value=final_value,
        business_process_impact=business_process_impact,
        legal_requirements_impact=legal_requirements_impact,
        financial_losses_impact=financial_losses_impact,
        reputation_impact=reputation_impact,
        asset_cost=data.get('asset_cost'),
        asset_cost_rating=asset_cost_rating,
        dependency_value=dependency_value,
        impact_matrix=data.get('impact_matrix')
    )
    
    db.session.add(asset)
    db.session.commit()
    
    
    # Сохраняем данные о воздействии на свойства ИБ
    security_property_impacts = data.get('security_property_impacts', [])
    if security_property_impacts:
        context_id = data.get('context_id')
        if context_id:
            # Получаем критерии влияния для контекста
            context_criteria = ContextImpactCriterion.query.filter_by(context_id=context_id).all()
            context_criteria_list = [cc.impact_criterion for cc in context_criteria]
            
            # Если нет критериев для контекста, получаем все критерии
            if not context_criteria_list:
                all_criteria = ImpactCriterion.query.all()
                context_criteria_list = all_criteria
                print(f"Нет критериев для контекста {context_id}, используем все критерии: {len(context_criteria_list)}")
            else:
                print(f"Найдено критериев влияния для контекста: {len(context_criteria_list)}")
            
            print(f"Данные для сохранения: {security_property_impacts}")
            
            for impact_data in security_property_impacts:
                security_property = impact_data.get('security_property')
                criterion_index = impact_data.get('criterion_index')
                impact_value = impact_data.get('impact_value')
                
                print(f"Обработка: security_property={security_property}, criterion_index={criterion_index}, impact_value={impact_value}")
                
                # Проверяем, есть ли критерий по индексу
                if (security_property and criterion_index is not None and
                    impact_value and criterion_index < len(context_criteria_list)):
                    
                    criterion = context_criteria_list[criterion_index]
                    print(f"Найден критерий: {criterion.name} (ID: {criterion.id})")
                    
                    # Создаем запись о воздействии
                    asset_impact = AssetSecurityPropertyImpact(
                        asset_id=asset.id,
                        security_property=security_property,
                        impact_criterion_id=criterion.id,
                        impact_value=impact_value
                    )
                    db.session.add(asset_impact)
                    print(f"Добавлена запись: asset_id={asset.id}, security_property={security_property}, impact_criterion_id={criterion.id}, impact_value={impact_value}")
                # Альтернативно, если в данных есть напрямую impact_criterion_id
                elif security_property and impact_data.get('impact_criterion_id') and impact_value:
                    # Используем напрямую указанный ID критерия
                    impact_criterion_id = impact_data.get('impact_criterion_id')
                    # Проверяем, что критерий существует
                    criterion = ImpactCriterion.query.get(impact_criterion_id)
                    if criterion:
                        asset_impact = AssetSecurityPropertyImpact(
                            asset_id=asset.id,
                            security_property=security_property,
                            impact_criterion_id=impact_criterion_id,
                            impact_value=impact_value
                        )
                        db.session.add(asset_impact)
                        print(f"Добавлена запись (по ID): asset_id={asset.id}, security_property={security_property}, impact_criterion_id={impact_criterion_id}, impact_value={impact_value}")
                # Если нет критериев вообще, выводим предупреждение
                elif len(context_criteria_list) == 0:
                    print(f"ПРЕДУПРЕЖДЕНИЕ: Нет доступных критериев для сохранения данных о воздействии для актива {asset.id}")
    
    db.session.commit()
    
    # Если установлено dependency_value, обновляем зависимые активы
    if dependency_value is not None:
        update_dependent_assets(asset.id, dependency_value, set())
        db.session.commit()
    
    # Пересчитываем зависимости для этого актива (учитываем активы, от которых он зависит)
    recalculate_asset_dependencies(asset.id)
    
    return jsonify(asset.to_dict()), 201

@bp.route('/<int:asset_id>', methods=['PUT'])
def update_asset(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    data = request.get_json()
    
    asset.context_id = data.get('context_id', asset.context_id)
    asset.name = data.get('name', asset.name)
    asset.description = data.get('description', asset.description)
    asset.type = data.get('type', asset.type)
    asset.properties = data.get('properties', asset.properties)
    asset.impact_score = data.get('impact_score', asset.impact_score)
    asset.impact_matrix = data.get('impact_matrix', asset.impact_matrix)
    
    # Обработка полей с CHECK constraint - преобразуем пустые строки в None
    cost_value = data.get('cost_value')
    if cost_value == '':
        cost_value = None
    else:
        cost_value = cost_value if cost_value is not None else asset.cost_value
    asset.cost_value = cost_value
    
    value_without_dependencies = data.get('value_without_dependencies')
    if value_without_dependencies == '':
        value_without_dependencies = None
    else:
        value_without_dependencies = value_without_dependencies if value_without_dependencies is not None else asset.value_without_dependencies
    asset.value_without_dependencies = value_without_dependencies
    
    final_value = data.get('final_value')
    if final_value == '':
        final_value = None
    else:
        final_value = final_value if final_value is not None else asset.final_value
    asset.final_value = final_value
    
    asset_cost_rating = data.get('asset_cost_rating')
    if asset_cost_rating == '':
        asset_cost_rating = None
    else:
        asset_cost_rating = asset_cost_rating if asset_cost_rating is not None else asset.asset_cost_rating
    asset.asset_cost_rating = asset_cost_rating
    
    dependency_value = data.get('dependency_value')
    if dependency_value == '':
        dependency_value = None
    else:
        dependency_value = dependency_value if dependency_value is not None else asset.dependency_value
    old_dependency_value = asset.dependency_value
    
    # Обновляем dependency_value только если новое значение выше текущего
    if dependency_value:
        if asset.dependency_value is None:
            asset.dependency_value = dependency_value
        else:
            # Сравниваем значения: низкая < средняя < высокая
            priority_map = {'низкая': 1, 'средняя': 2, 'высокая': 3}
            current_priority = priority_map.get(asset.dependency_value, 0)
            new_priority = priority_map.get(dependency_value, 0)
            if new_priority >= current_priority:  # Устанавливаем новое значение, если оно не ниже текущего
                asset.dependency_value = dependency_value
    
    # Если dependency_value изменилось, обновляем зависимые активы
    if old_dependency_value != dependency_value and dependency_value is not None:
        update_dependent_assets(asset.id, dependency_value, set())
        db.session.commit()
    else:
        # Если dependency_value не изменилось, просто делаем commit
        db.session.commit()
    
    # Обработка полей с CHECK constraint для обновления - преобразуем пустые строки в None
    business_process_impact = data.get('business_process_impact')
    if business_process_impact == '':
        business_process_impact = None
    else:
        business_process_impact = business_process_impact if business_process_impact is not None else asset.business_process_impact
    asset.business_process_impact = business_process_impact
      
    legal_requirements_impact = data.get('legal_requirements_impact')
    if legal_requirements_impact == '':
        legal_requirements_impact = None
    else:
        legal_requirements_impact = legal_requirements_impact if legal_requirements_impact is not None else asset.legal_requirements_impact
    asset.legal_requirements_impact = legal_requirements_impact
      
    financial_losses_impact = data.get('financial_losses_impact')
    if financial_losses_impact == '':
        financial_losses_impact = None
    else:
        financial_losses_impact = financial_losses_impact if financial_losses_impact is not None else asset.financial_losses_impact
    asset.financial_losses_impact = financial_losses_impact
      
    reputation_impact = data.get('reputation_impact')
    if reputation_impact == '':
        reputation_impact = None
    else:
        reputation_impact = reputation_impact if reputation_impact is not None else asset.reputation_impact
    asset.reputation_impact = reputation_impact
      
    asset.asset_cost = data.get('asset_cost', asset.asset_cost)
    asset.updated_at = datetime.utcnow()
    
    # Удаляем старые данные о воздействии на свойства ИБ
    old_impacts = AssetSecurityPropertyImpact.query.filter_by(asset_id=asset_id).all()
    for old_impact in old_impacts:
        db.session.delete(old_impact)
    
    # Сохраняем новые данные о воздействии на свойства ИБ
    security_property_impacts = data.get('security_property_impacts', [])
    if security_property_impacts:
        context_id = data.get('context_id')
        if context_id:
            # Получаем критерии влияния для контекста
            context_criteria = ContextImpactCriterion.query.filter_by(context_id=context_id).all()
            context_criteria_list = [cc.impact_criterion for cc in context_criteria]
            
            # Если нет критериев для контекста, получаем все критерии
            if not context_criteria_list:
                all_criteria = ImpactCriterion.query.all()
                context_criteria_list = all_criteria
                print(f"PUT - Нет критериев для контекста {context_id}, используем все критерии: {len(context_criteria_list)}")
            else:
                print(f"PUT - Найдено критериев влияния для контекста: {len(context_criteria_list)}")
            
            print(f"PUT - Данные для сохранения: {security_property_impacts}")
            
            for impact_data in security_property_impacts:
                security_property = impact_data.get('security_property')
                criterion_index = impact_data.get('criterion_index')
                impact_value = impact_data.get('impact_value')
                
                print(f"PUT - Обработка: security_property={security_property}, criterion_index={criterion_index}, impact_value={impact_value}")
                
                # Проверяем, есть ли критерий по индексу
                if (security_property and criterion_index is not None and
                    impact_value and criterion_index < len(context_criteria_list)):
                    
                    criterion = context_criteria_list[criterion_index]
                    print(f"PUT - Найден критерий: {criterion.name} (ID: {criterion.id})")
                    
                    # Создаем запись о воздействии
                    asset_impact = AssetSecurityPropertyImpact(
                        asset_id=asset.id,
                        security_property=security_property,
                        impact_criterion_id=criterion.id,
                        impact_value=impact_value
                    )
                    db.session.add(asset_impact)
                    print(f"PUT - Добавлена запись: asset_id={asset.id}, security_property={security_property}, impact_criterion_id={criterion.id}, impact_value={impact_value}")
                # Альтернативно, если в данных есть напрямую impact_criterion_id
                elif security_property and impact_data.get('impact_criterion_id') and impact_value:
                    # Используем напрямую указанный ID критерия
                    impact_criterion_id = impact_data.get('impact_criterion_id')
                    # Проверяем, что критерий существует
                    criterion = ImpactCriterion.query.get(impact_criterion_id)
                    if criterion:
                        asset_impact = AssetSecurityPropertyImpact(
                            asset_id=asset.id,
                            security_property=security_property,
                            impact_criterion_id=impact_criterion_id,
                            impact_value=impact_value
                        )
                        db.session.add(asset_impact)
                        print(f"PUT - Добавлена запись (по ID): asset_id={asset.id}, security_property={security_property}, impact_criterion_id={impact_criterion_id}, impact_value={impact_value}")
                # Если нет критериев вообще, выводим предупреждение
                elif len(context_criteria_list) == 0:
                    print(f"PUT - ПРЕДУПРЕЖДЕНИЕ: Нет доступных критериев для сохранения данных о воздействии для актива {asset.id}")
    
    db.session.commit()
    
    # Пересчитываем зависимости для этого актива (учитываем активы, от которых он зависит)
    recalculate_asset_dependencies(asset.id)
      
    return jsonify(asset.to_dict())

@bp.route('/<int:asset_id>', methods=['DELETE'])
def delete_asset(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    
    # Удаление связанных результатов оценки ценности
    from app.models.asset_value_result import AssetValueResult
    value_results = AssetValueResult.query.filter_by(asset_id=asset_id).all()
    for result in value_results:
        db.session.delete(result)
    
    # Удаление связанных зависимостей
    dependencies = AssetDependency.query.filter(
        (AssetDependency.asset_id == asset_id) |
        (AssetDependency.depends_on_asset_id == asset_id)
    ).all()
    for dep in dependencies:
        db.session.delete(dep)
    
    # Удаление связанных оценок воздействия
    assessments = AssetImpactAssessment.query.filter_by(asset_id=asset_id).all()
    for assessment in assessments:
        db.session.delete(assessment)
    
    db.session.delete(asset)
    db.session.commit()
    
    return '', 204

@bp.route('/value-assessment', methods=['GET'])
def value_assessment():
    from flask import render_template
    assets = Asset.query.all()
    return render_template('assets/new_value_assessment.html', assets=[asset.to_dict() for asset in assets])

@bp.route('/value-results', methods=['GET'])
def value_results():
    from flask import render_template
    return render_template('assets/value_results.html')

@bp.route('/dependencies', methods=['GET'])
def asset_dependencies():
    from flask import render_template
    assets = Asset.query.all()
    return render_template('assets/dependencies.html', assets=assets)