from flask import Blueprint, request, jsonify
from app import db
from app.models import AssetDependency, Asset

bp = Blueprint('asset_dependency_bp', __name__, url_prefix='/api/asset-dependencies')

@bp.route('/', methods=['GET'])
def get_asset_dependencies():
    """Получить все зависимости активов"""
    asset_id = request.args.get('asset_id')
    depends_on_asset_id = request.args.get('depends_on_asset_id')
    
    query = AssetDependency.query
    
    if asset_id:
        query = query.filter_by(asset_id=asset_id)
    if depends_on_asset_id:
        query = query.filter_by(depends_on_asset_id=depends_on_asset_id)
    
    dependencies = query.all()
    return jsonify([dep.to_dict() for dep in dependencies])

@bp.route('/', methods=['POST'])
def create_asset_dependency():
    """Создать новую зависимость актива"""
    data = request.get_json()
    
    # Проверяем, что зависимости не существует
    existing = AssetDependency.query.filter_by(
        asset_id=data.get('asset_id'),
        depends_on_asset_id=data.get('depends_on_asset_id')
    ).first()
    
    if existing:
        return jsonify({'error': 'Dependency already exists'}), 400
    
    dependency = AssetDependency(
        asset_id=data.get('asset_id'),
        depends_on_asset_id=data.get('depends_on_asset_id'),
        relationship_type=data.get('relationship_type', '+')
    )
    
    db.session.add(dependency)
    db.session.commit()
    
    return jsonify(dependency.to_dict()), 201

@bp.route('/<int:dep_id>', methods=['PUT'])
def update_asset_dependency(dep_id):
    """Обновить зависимость актива"""
    dependency = AssetDependency.query.get_or_404(dep_id)
    data = request.get_json()
    
    dependency.relationship_type = data.get('relationship_type', dependency.relationship_type)
    
    db.session.commit()
    return jsonify(dependency.to_dict())

@bp.route('/<int:dep_id>', methods=['DELETE'])
def delete_asset_dependency(dep_id):
    """Удалить зависимость актива"""
    dependency = AssetDependency.query.get_or_404(dep_id)
    db.session.delete(dependency)
    db.session.commit()
    return '', 204

@bp.route('/by-asset/<int:asset_id>', methods=['GET'])
def get_dependencies_by_asset(asset_id):
    """Получить зависимости для конкретного актива"""
    dependencies = AssetDependency.query.filter_by(asset_id=asset_id).all()
    return jsonify([dep.to_dict() for dep in dependencies])

@bp.route('/for-asset/<int:asset_id>', methods=['GET'])
def get_dependencies_for_asset(asset_id):
    """Получить активы, от которых зависит конкретный актив"""
    dependencies = AssetDependency.query.filter_by(depends_on_asset_id=asset_id).all()
    return jsonify([dep.to_dict() for dep in dependencies])

@bp.route('/bulk-update', methods=['POST'])
def bulk_update_dependencies():
    """Массовое обновление зависимостей активов"""
    data = request.get_json()
    dependencies_data = data.get('dependencies', [])
    
    # Получаем все уникальные asset_id из текущих зависимостей в БД
    all_existing_deps = AssetDependency.query.all()
    all_asset_ids_with_deps = set([dep.asset_id for dep in all_existing_deps])
    
    # Добавляем asset_id из новых данных
    new_asset_ids = set([dep['asset_id'] for dep in dependencies_data])
    all_affected_asset_ids = all_asset_ids_with_deps.union(new_asset_ids)
    
    # Также добавляем все активы, чтобы очистить dependency_value у тех, кто потерял зависимости
    all_assets = Asset.query.all()
    for asset in all_assets:
        all_affected_asset_ids.add(asset.id)
    
    # Удаляем ВСЕ существующие зависимости
    AssetDependency.query.delete()
    db.session.commit()
    
    # Создаем новые зависимости
    for dep_data in dependencies_data:
        dependency = AssetDependency(
            asset_id=dep_data.get('asset_id'),
            depends_on_asset_id=dep_data.get('depends_on_asset_id'),
            relationship_type=dep_data.get('relationship_type', '+')
        )
        db.session.add(dependency)
    
    db.session.commit()
    
    # Пересчитываем dependency_value для всех активов
    for asset_id in all_affected_asset_ids:
        asset = Asset.query.get(asset_id)
        if not asset:
            continue
            
        # Проверяем, есть ли у актива зависимости после обновления
        asset_deps = AssetDependency.query.filter_by(asset_id=asset_id).all()
        
        if not asset_deps:
            # Если зависимостей нет, очищаем dependency_value
            asset.dependency_value = None
        else:
            # Если есть зависимости, пересчитываем dependency_value
            # Собираем все связанные активы (сам актив + активы, от которых он зависит)
            related_asset_ids = [asset_id]
            for dep in asset_deps:
                related_asset_ids.append(dep.depends_on_asset_id)
            
            # Находим максимальную ценность без зависимостей среди всех связанных активов
            max_value_without_deps = None
            priority_map = {'Н': 1, 'С': 2, 'В': 3}
            max_priority = 0
            
            for related_id in related_asset_ids:
                related_asset = Asset.query.get(related_id)
                if related_asset and related_asset.value_without_dependencies:
                    asset_priority = priority_map.get(related_asset.value_without_dependencies, 0)
                    if asset_priority > max_priority:
                        max_priority = asset_priority
                        max_value_without_deps = related_asset.value_without_dependencies
            
            # Преобразуем в формат для dependency_value
            if max_value_without_deps:
                dependency_value_map = {'Н': 'низкая', 'С': 'средняя', 'В': 'высокая'}
                asset.dependency_value = dependency_value_map.get(max_value_without_deps, 'средняя')
            else:
                asset.dependency_value = None
    
    db.session.commit()
    
    return jsonify({'success': True})