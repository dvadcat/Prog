from flask import Blueprint, request, jsonify, render_template
from app import db
from app.models import Incident, Risk, RiskTreatmentPlan, Asset, Threat, Vulnerability
from datetime import datetime

bp = Blueprint('incident_bp', __name__, url_prefix='/api/incidents')

@bp.route('/', methods=['GET'])
def get_incidents():
    incidents = Incident.query.all()
    return jsonify([incident.to_dict() for incident in incidents])

@bp.route('/<int:incident_id>', methods=['GET'])
def get_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    return jsonify(incident.to_dict())

@bp.route('/', methods=['POST'])
def create_incident():
    data = request.get_json()
    
    # Проверяем, есть ли массивы для множественного выбора
    assets = data.get('assets', [])
    threats = data.get('threats', [])
    vulnerabilities = data.get('vulnerabilities', [])
    
    created_incidents = []
    
    # Если есть массивы, создаем инциденты для всех комбинаций
    if assets and threats and vulnerabilities:
        # Получаем максимальный ID инцидента из базы данных
        max_incident = Incident.query.order_by(Incident.id.desc()).first()
        next_id = (max_incident.id + 1) if max_incident else 1
        
        for asset_id in assets:
            for threat_id in threats:
                for vulnerability_id in vulnerabilities:
                    # Генерируем обозначение сценария на основе следующего ID
                    scenario_name = f"СИ{next_id}"
                    
                    incident = Incident(
                        asset_id=asset_id,
                        threat_id=threat_id,
                        vulnerability_id=vulnerability_id,
                        operational_impact=data.get('operational_impact'),
                        business_impact=data.get('business_impact'),
                        impact_level=data.get('impact_level') or None,  # По умолчанию None
                        scenario_name=scenario_name
                    )
                    
                    db.session.add(incident)
                    created_incidents.append(incident)
                    next_id += 1  # Увеличиваем счетчик для следующего инцидента
        
        db.session.commit()
        
        # Возвращаем первый созданный инцидент как основной
        return jsonify(created_incidents[0].to_dict()), 201
    else:
        # Одиночное создание (обратная совместимость)
        incident = Incident(
            asset_id=data.get('asset_id'),
            threat_id=data.get('threat_id'),
            vulnerability_id=data.get('vulnerability_id'),
            operational_impact=data.get('operational_impact'),
            business_impact=data.get('business_impact'),
            impact_level=data.get('impact_level') or None,
            scenario_name=data.get('scenario_name')
        )
        
        db.session.add(incident)
        db.session.commit()
        
        return jsonify(incident.to_dict()), 201

@bp.route('/<int:incident_id>', methods=['PUT'])
def update_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    data = request.get_json()
    
    incident.asset_id = data.get('asset_id', incident.asset_id)
    incident.threat_id = data.get('threat_id', incident.threat_id)
    incident.vulnerability_id = data.get('vulnerability_id', incident.vulnerability_id)
    incident.operational_impact = data.get('operational_impact', incident.operational_impact)
    incident.business_impact = data.get('business_impact', incident.business_impact)
    
    # Конвертируем пустые строки в None для полей с CHECK constraints
    impact_level = data.get('impact_level', incident.impact_level)
    incident.impact_level = impact_level if impact_level else None
    
    scenario_probability = data.get('scenario_probability', incident.scenario_probability)
    incident.scenario_probability = scenario_probability if scenario_probability else None
    
    incident.scenario_name = data.get('scenario_name', incident.scenario_name)
    incident.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify(incident.to_dict())

@bp.route('/<int:incident_id>', methods=['DELETE'])
def delete_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    
    # Удаление связанных рисков
    risks = Risk.query.filter_by(incident_id=incident_id).all()
    for risk in risks:
        db.session.delete(risk)
    
    # Удаление связанных планов обработки
    treatment_plans = RiskTreatmentPlan.query.filter_by(incident_id=incident_id).all()
    for plan in treatment_plans:
        db.session.delete(plan)
    
    db.session.delete(incident)
    db.session.commit()
    
    return '', 204

# HTML маршруты для интерфейса
@bp.route('/list', methods=['GET'])
def incidents_list_page():
    return render_template('incidents/list.html')

@bp.route('/create', methods=['GET'])
def create_incident_page():
    return render_template('incidents/form.html')

@bp.route('/<int:incident_id>/edit', methods=['GET'])
def edit_incident_page(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    return render_template('incidents/form.html', incident=incident)

@bp.route('/<int:incident_id>/tables', methods=['GET'])
def incident_tables_page(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    return render_template('incidents/tables.html', incident=incident)

@bp.route('/<int:incident_id>/edit-consequences', methods=['GET'])
def edit_incident_consequences_page(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    return render_template('incidents/edit_consequences.html', incident=incident)

@bp.route('/summary-tables', methods=['GET'], endpoint='summary_tables')
def summary_tables_page():
    incidents = Incident.query.all()
    return render_template('incidents/summary_tables.html', incidents=incidents)