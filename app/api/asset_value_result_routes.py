from flask import Blueprint, request, jsonify
from app import db
from app.models import AssetValueResult, Asset

bp = Blueprint('asset_value_result_bp', __name__, url_prefix='/api/asset-value-results')

@bp.route('/', methods=['GET'])
def get_asset_value_results():
    """Получить все результаты оценки ценности активов"""
    asset_id = request.args.get('asset_id')
    query = AssetValueResult.query
    
    if asset_id:
        query = query.filter_by(asset_id=asset_id)
    
    results = query.all()
    result_dicts = []
    for result in results:
        result_dict = result.to_dict()
        # Добавляем данные актива в результат
        result_dict['asset'] = result.asset.to_dict() if result.asset else None
        result_dicts.append(result_dict)
    return jsonify(result_dicts)

@bp.route('/', methods=['POST'])
def create_asset_value_result():
    """Создать новый результат оценки ценности актива или обновить существующий"""
    data = request.get_json()
    
    asset_id = data.get('asset_id')
    if not asset_id:
        return jsonify({'error': 'Asset ID is required'}), 400
    
    # Проверяем, существует ли уже запись для этого актива
    existing_result = AssetValueResult.query.filter_by(asset_id=asset_id).first()
    
    if existing_result:
        # Обновляем существующую запись
        existing_result.type = data.get('type', existing_result.type)
        existing_result.value_without_dependencies = data.get('value_without_dependencies', existing_result.value_without_dependencies)
        existing_result.value_with_dependencies = data.get('value_with_dependencies', existing_result.value_with_dependencies)
        existing_result.final_value = data.get('final_value', existing_result.final_value)
        
        db.session.commit()
        result = existing_result
    else:
        # Создаем новую запись
        asset = Asset.query.get(asset_id)
        if not asset:
            return jsonify({'error': 'Asset not found'}), 404
        
        result = AssetValueResult(
            asset_id=asset_id,
            type=asset.type,
            value_without_dependencies=data.get('value_without_dependencies'),
            value_with_dependencies=data.get('value_with_dependencies'),
            final_value=data.get('final_value')
        )
        
        db.session.add(result)
        db.session.commit()
    
    result_dict = result.to_dict()
    result_dict['asset'] = result.asset.to_dict() if result.asset else None
    return jsonify(result_dict), 201

@bp.route('/<int:result_id>', methods=['PUT'])
def update_asset_value_result(result_id):
    """Обновить результат оценки ценности актива"""
    result = AssetValueResult.query.get_or_404(result_id)
    data = request.get_json()
    
    result.value_without_dependencies = data.get('value_without_dependencies', result.value_without_dependencies)
    result.value_with_dependencies = data.get('value_with_dependencies', result.value_with_dependencies)
    result.final_value = data.get('final_value', result.final_value)
    
    db.session.commit()
    result_dict = result.to_dict()
    result_dict['asset'] = result.asset.to_dict() if result.asset else None
    return jsonify(result_dict)

@bp.route('/<int:result_id>', methods=['DELETE'])
def delete_asset_value_result(result_id):
    """Удалить результат оценки ценности актива"""
    result = AssetValueResult.query.get_or_404(result_id)
    db.session.delete(result)
    db.session.commit()
    return '', 204

@bp.route('/by-asset/<int:asset_id>', methods=['GET'])
def get_results_by_asset(asset_id):
    """Получить результаты оценки для конкретного актива"""
    results = AssetValueResult.query.filter_by(asset_id=asset_id).all()
    result_dicts = []
    for result in results:
        result_dict = result.to_dict()
        result_dict['asset'] = result.asset.to_dict() if result.asset else None
        result_dicts.append(result_dict)
    return jsonify(result_dicts)

@bp.route('/summary', methods=['GET'])
def get_value_summary():
    """Получить сводку по ценности активов"""
    results = AssetValueResult.query.all()
    
    summary = []
    for result in results:
        summary.append({
            'type': result.type,
            'asset_name': result.asset.name if result.asset else 'Unknown',
            'final_value': result.final_value
        })
    
    return jsonify(summary)