from flask import Blueprint, request, jsonify, render_template
from app import db
from app.models import Threat, AssetThreat
from datetime import datetime

bp = Blueprint('threat_bp', __name__, url_prefix='/api/threats')

@bp.route('/', methods=['GET'])
def get_threats():
    # Параметр для фильтрации только актуальных угроз
    only_relevant = request.args.get('only_relevant', 'false').lower() == 'true'
    
    if only_relevant:
        threats = Threat.query.filter_by(is_relevant=True).all()
    else:
        threats = Threat.query.all()
    
    return jsonify([threat.to_dict() for threat in threats])

@bp.route('/main', methods=['GET'])
def threats_main():
    threats = Threat.query.all()
    return render_template('threats/main.html', threats=threats)

@bp.route('/info-tables', methods=['GET'])
def threat_info_tables():
    threats = Threat.query.all()
    return render_template('threats/threat_info_tables.html', threats=threats)

@bp.route('/asset-mapping', methods=['GET'])
def asset_threat_mapping():
    threats = Threat.query.all()
    return render_template('threats/asset_threat_mapping.html', threats=threats)

@bp.route('/active-threats', methods=['GET'])
def active_threats_list():
    threats = Threat.query.all()
    return render_template('threats/active_threats_list.html', threats=threats)

@bp.route('/source-assessment', methods=['GET'])
def source_assessment():
    threats = Threat.query.all()
    return render_template('threats/source_assessment.html', threats=threats)

@bp.route('/source-assessment-results', methods=['GET'])
def source_assessment_results():
    threats = Threat.query.all()
    return render_template('threats/source_assessment_results.html', threats=threats)

@bp.route('/probability-criteria', methods=['GET'])
def probability_criteria():
    threats = Threat.query.all()
    return render_template('threats/probability_criteria.html', threats=threats)

@bp.route('/probability-calculation', methods=['GET'])
def probability_calculation():
    threats = Threat.query.all()
    return render_template('threats/probability_calculation.html', threats=threats)

@bp.route('/probability-final-calculation', methods=['GET'])
def probability_final_calculation():
    threats = Threat.query.all()
    return render_template('threats/probability_final_calculation.html', threats=threats)

@bp.route('/asset-probability-evaluation', methods=['GET'])
def asset_probability_evaluation():
    threats = Threat.query.all()
    return render_template('threats/asset_probability_evaluation.html', threats=threats)

@bp.route('/asset-probability-table', methods=['GET'])
def asset_probability_table():
    return render_template('threats/asset_probability_table.html')

@bp.route('/add-wizard', methods=['GET'])
def add_threat_wizard_start():
    threats = Threat.query.all()
    
    # Импортируем модель Asset
    from app.models import Asset
    assets = Asset.query.all()
    
    return render_template('threats/add_threat_wizard.html', threats=threats, assets=assets, step=0, progress=0, step_title='Выбор угрозы')

@bp.route('/add-wizard/<int:step_num>', methods=['GET'])
def add_threat_wizard_step(step_num):
    threats = Threat.query.all()
    
    # Импортируем модель Asset
    from app.models import Asset
    assets = Asset.query.all()
    
    step_titles = {
        0: 'Выбор угрозы',
        1: 'Описание угрозы',
        2: 'Источники угрозы',
        3: 'Объекты воздействия',
        4: 'Последствия реализации угрозы',
        5: 'Соответствие между активами и угрозами',
        6: 'Перечень актуальных угроз ИБ активов',
        7: 'Оценка признака "Источник угрозы ИБ"',
        8: 'Результаты оценки признака "Источник угрозы ИБ"',
        9: 'Критерии оценки вероятности реализации угрозы',
        10: 'Расчет вероятности реализации угрозы',
        11: 'Качественное и количественное значения',
        12: 'Оценка вероятности для каждого актива'
    }
    
    progress = min(100, step_num * 8)  # Примерный расчет прогресса
    
    return render_template('threats/add_threat_wizard.html', threats=threats, assets=assets, step=step_num, progress=progress, step_title=step_titles.get(step_num, ''))

@bp.route('/<int:threat_id>', methods=['GET'])
def get_threat(threat_id):
    threat = Threat.query.get_or_404(threat_id)
    return jsonify(threat.to_dict())

@bp.route('/', methods=['POST'])
def create_threat():
    data = request.get_json()
    
    # Преобразуем строки дат в объекты дат
    published_at = None
    if data.get('published_at'):
        published_at = datetime.fromisoformat(data['published_at'].replace('Z', '+00:00')).date()
    
    updated_at = None
    if data.get('updated_at'):
        updated_at = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00')).date()
    
    threat = Threat(
        name=data.get('name'),
        description=data.get('description'),
        source=data.get('source'),
        target_object=data.get('target_object'),
        confidentiality_violation=data.get('confidentiality_violation', False),
        integrity_violation=data.get('integrity_violation', False),
        availability_violation=data.get('availability_violation', False),
        likelihood=data.get('likelihood'),
        published_at=published_at,
        updated_at=updated_at,
        imported_from_bdu=data.get('imported_from_bdu', False),
        is_relevant=data.get('is_relevant', False),
        step5=data.get('step5')
    )
    
    db.session.add(threat)
    db.session.commit()
    
    return jsonify(threat.to_dict()), 201

@bp.route('/<int:threat_id>', methods=['PUT'])
def update_threat(threat_id):
    threat = Threat.query.get_or_404(threat_id)
    data = request.get_json()
    
    threat.name = data.get('name', threat.name)
    threat.description = data.get('description', threat.description)
    threat.source = data.get('source', threat.source)
    threat.target_object = data.get('target_object', threat.target_object)
    threat.confidentiality_violation = data.get('confidentiality_violation', threat.confidentiality_violation)
    threat.integrity_violation = data.get('integrity_violation', threat.integrity_violation)
    threat.availability_violation = data.get('availability_violation', threat.availability_violation)
    threat.likelihood = data.get('likelihood', threat.likelihood)
    threat.step5 = data.get('step5', threat.step5)
    threat.is_relevant = data.get('is_relevant', threat.is_relevant)
    
    # Обработка дат
    if 'published_at' in data:
        if data['published_at']:
            threat.published_at = datetime.fromisoformat(data['published_at'].replace('Z', '+00:00')).date()
        else:
            threat.published_at = None
    
    if 'updated_at' in data:
        if data['updated_at']:
            threat.updated_at = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00')).date()
        else:
            threat.updated_at = None
    
    threat.imported_from_bdu = data.get('imported_from_bdu', threat.imported_from_bdu)
    
    db.session.commit()
    
    return jsonify(threat.to_dict())

@bp.route('/source-assessment', methods=['POST'])
def save_source_assessment():
    data = request.get_json()
    threat_id = data.get('threat_id')
    assessment = data.get('assessment')
    scores = data.get('scores')

    if not threat_id or assessment is None:
        return jsonify({'error': 'threat_id and assessment required'}), 400

    # Проверяем, существует ли угроза
    threat = Threat.query.get(threat_id)
    if not threat:
        return jsonify({'error': 'Threat not found'}), 404

    # Сохраняем или обновляем оценку источника угрозы
    # Для простоты сохраняем в JSON поле threat.source_assessment
    import json
    source_assessment_data = {
        'assessment': assessment,
        'scores': scores,
        'calculated_at': datetime.now().isoformat()
    }
    
    threat.source_assessment = json.dumps(source_assessment_data)
    db.session.commit()

    return jsonify({'message': 'Source assessment saved successfully'}), 200

@bp.route('/probability-assessment', methods=['POST'])
def save_probability_assessment():
    data = request.get_json()
    threat_id = data.get('threat_id')
    assessment = data.get('assessment')
    scores = data.get('scores')

    if not threat_id or assessment is None:
        return jsonify({'error': 'threat_id and assessment required'}), 400

    # Проверяем, существует ли угроза
    threat = Threat.query.get(threat_id)
    if not threat:
        return jsonify({'error': 'Threat not found'}), 404

    # Сохраняем или обновляем оценку вероятности реализации угрозы
    # Для простоты сохраняем в JSON поле threat.probability_assessment
    import json
    probability_assessment_data = {
        'assessment': assessment,
        'scores': scores,
        'calculated_at': datetime.now().isoformat()
    }
    
    threat.probability_assessment = json.dumps(probability_assessment_data)
    db.session.commit()

    return jsonify({'message': 'Probability assessment saved successfully'}), 200

@bp.route('/<int:threat_id>/relevance', methods=['PUT'])
def update_threat_relevance(threat_id):
    threat = Threat.query.get_or_404(threat_id)
    data = request.get_json()
    
    # Обновляем статус актуальности
    threat.is_relevant = data.get('is_relevant', False)
    
    db.session.commit()
    
    return jsonify({'message': 'Threat relevance updated successfully', 'is_relevant': threat.is_relevant}), 200

@bp.route('/<int:threat_id>', methods=['DELETE'])
def delete_threat(threat_id):
    threat = Threat.query.get_or_404(threat_id)
    
    # Удаление связанных записей в asset_threats
    asset_threats = AssetThreat.query.filter_by(threat_id=threat_id).all()
    for asset_threat in asset_threats:
        db.session.delete(asset_threat)
    
    db.session.delete(threat)
    db.session.commit()
    
    return '', 204

@bp.route('/asset-probability-assessments', methods=['GET'])
def get_asset_probability_assessments():
    """
    Получение всех сохраненных оценок вероятности реализации угроз для активов
    """
    from app.models import ThreatAssessment
    assessments = ThreatAssessment.query.all()
    return jsonify([a.to_dict() for a in assessments])

@bp.route('/save-asset-probability-assessment', methods=['POST'])
def save_asset_probability_assessment():
    """
    Сохранение результатов оценки вероятности реализации угрозы для активов
    """
    try:
        data = request.get_json()
        print(f"[DEBUG] Received data for saving assessments: {data}")
        
        from app.models import ThreatAssessment
        
        assessments_list = data.get('assessments', [])
        print(f"[DEBUG] Number of assessments to save: {len(assessments_list)}")
        
        # Проходим по всем оценкам из данных
        for assessment_data in assessments_list:
            print(f"[DEBUG] Processing assessment: asset_id={assessment_data.get('asset_id')}, threat_id={assessment_data.get('threat_id')}, score={assessment_data.get('score')}, level={assessment_data.get('level')}")
            
            # Проверяем, существует ли уже оценка для этой связки актив-угроза
            existing = ThreatAssessment.query.filter_by(
                asset_id=assessment_data['asset_id'],
                threat_id=assessment_data['threat_id']
            ).first()
            
            if existing:
                # Обновляем существующую оценку
                print(f"[DEBUG] Updating existing assessment ID={existing.id}")
                existing.score = assessment_data['score']
                existing.assessment = assessment_data.get('level', '')
            else:
                # Создаем новую оценку
                print(f"[DEBUG] Creating new assessment")
                threat_assessment = ThreatAssessment(
                    asset_id=assessment_data['asset_id'],
                    threat_id=assessment_data['threat_id'],
                    score=assessment_data['score'],
                    assessment=assessment_data.get('level', '')
                )
                db.session.add(threat_assessment)
        
        db.session.commit()
        print(f"[DEBUG] Successfully committed {len(assessments_list)} assessments to database")
        
        # Verify the data was saved
        saved_count = ThreatAssessment.query.count()
        print(f"[DEBUG] Total assessments in database after save: {saved_count}")
        
        return jsonify({'message': 'Оценки вероятности реализации угроз успешно сохранены', 'count': len(assessments_list)}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Error saving assessments: {str(e)}")
        return jsonify({'error': f'Ошибка сохранения оценок: {str(e)}'}), 500