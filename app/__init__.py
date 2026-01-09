from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from app.config import Config

db = SQLAlchemy()

# Default impact criteria
DEFAULT_IMPACT_CRITERIA = [
    "Нарушение законодательных требований",
    "Нарушение договорных обязательств",
    "Нарушение функционирования бизнес-процессов",
    "Создание угрозы для безопасности внутренней и внешней среды",
    "Опасность для персонала и сотрудников объекта",
    "Финансовые потери",
    "Материальный ущерб",
    "Негативные последствия для репутации (\"неосязаемого капитала\")"
]


def create_default_impact_criteria():
    """Create default impact criteria if they don't exist"""
    from app.models import ImpactCriterion
    
    added_count = 0
    for criterion_name in DEFAULT_IMPACT_CRITERIA:
        existing = ImpactCriterion.query.filter_by(name=criterion_name).first()
        if not existing:
            criterion = ImpactCriterion(name=criterion_name)
            db.session.add(criterion)
            print(f"[ADDED] Impact criterion: {criterion_name}")
            added_count += 1
    
    if added_count > 0:
        db.session.commit()
        print(f"Total impact criteria added: {added_count}")
    
    return added_count


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    CORS(app)
    
    # Создаем дефолтные критерии влияния при первом запуске
    with app.app_context():
        try:
            # Проверяем существует ли таблица
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            if 'impact_criterion' in inspector.get_table_names():
                create_default_impact_criteria()
        except Exception as e:
            print(f"Warning: Could not create default criteria: {e}")
    
    # Регистрация blueprint'ов
    from app.api.context_routes import bp as context_bp
    from app.api.asset_routes import bp as asset_bp
    from app.api.asset_value_routes import bp as asset_value_bp
    from app.api.asset_dependency_routes import bp as asset_dependency_bp
    from app.api.damage_scale_routes import bp as damage_scale_bp
    from app.api.asset_security_property_impact_routes import bp as asset_security_property_impact_bp
    from app.api.asset_value_result_routes import bp as asset_value_result_bp
    from app.api.threat_routes import bp as threat_bp
    from app.api.vulnerability_routes import bp as vulnerability_bp
    from app.api.incident_routes import bp as incident_bp
    from app.api.risk_routes import bp as risk_bp
    from app.api.treatment_routes import bp as treatment_bp
    from app.api.report_routes import bp as reports_bp
    from app.api.report_management_routes import bp as report_management_bp
    
    app.register_blueprint(context_bp)
    app.register_blueprint(asset_bp)
    app.register_blueprint(asset_value_bp)
    app.register_blueprint(asset_dependency_bp)
    app.register_blueprint(damage_scale_bp)
    app.register_blueprint(asset_security_property_impact_bp)
    app.register_blueprint(asset_value_result_bp)
    app.register_blueprint(threat_bp)
    app.register_blueprint(vulnerability_bp)
    app.register_blueprint(incident_bp)
    app.register_blueprint(risk_bp)
    app.register_blueprint(treatment_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(report_management_bp)
    
    # Маршрут для главной страницы
    @app.route('/')
    def index():
        return render_template('index.html')
    
    # Маршруты для отображения списков сущностей
    @app.route('/contexts')
    def contexts_list():
        return render_template('contexts/list.html')
    
    @app.route('/contexts/create')
    def create_context():
        return render_template('contexts/form.html')
    
    @app.route('/contexts/<int:context_id>/edit')
    def edit_context(context_id):
        from app.models import Context
        context = Context.query.get_or_404(context_id)
        return render_template('contexts/form.html', context=context)
    
    @app.route('/assets')
    def assets_list():
        return render_template('assets/list.html')
    
    @app.route('/assets/create')
    def create_asset():
        from app.models import Asset
        from flask import request
        context_id = request.args.get('context_id', type=int)
        assets = Asset.query.all()
        return render_template('assets/form.html', asset=None, selected_context_id=context_id, assets=[a.to_dict() for a in assets])
    
    @app.route('/assets/<int:asset_id>/edit')
    def edit_asset(asset_id):
        from app.models import Asset
        asset = Asset.query.get_or_404(asset_id)
        assets = Asset.query.all()
        return render_template('assets/form.html', asset=asset, assets=[a.to_dict() for a in assets])
    
    @app.route('/assets/value-assessment')
    def asset_value_assessment():
        from flask import redirect
        return redirect('/api/assets/value-assessment')
    
    @app.route('/assets/value-results')
    def value_results():
        from flask import redirect
        return redirect('/api/assets/value-results')
    
    @app.route('/assets/dependencies')
    def asset_dependencies():
        from flask import redirect
        return redirect('/api/assets/dependencies')
    
    @app.route('/threats')
    def threats_list():
        from app.models import Threat
        threats = Threat.query.all()
        return render_template('threats/main.html', threats=threats)
    
    @app.route('/threats/create')
    def create_threat():
        from flask import redirect
        return redirect('/threats/add-wizard')
    
    @app.route('/threats/add-wizard')
    def add_threat_wizard():
        from app.models import Threat
        threats = Threat.query.all()
        return render_template('threats/add_threat_wizard.html', threats=threats, step=0, progress=0, step_title='Выбор угрозы')
    
    @app.route('/threats/add-wizard/<int:step>')
    def add_threat_wizard_step(step):
        from app.models import Threat, Asset
        from flask import request
        threats = Threat.query.all()
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

        progress = min(100, step * 8)  # 100/12 ≈ 8.33
        edit_threat_id = request.args.get('edit_threat_id', type=int)
        selected_threat = None
        if edit_threat_id:
            selected_threat = Threat.query.get(edit_threat_id)

        step_title = step_titles.get(step, '')
        if step == 1 and selected_threat:
            step_title = selected_threat.name

        return render_template('threats/add_threat_wizard.html', threats=threats, assets=assets, step=step, progress=progress, step_title=step_title, edit_threat_id=edit_threat_id, selected_threat=selected_threat)
    
    @app.route('/threats/<int:threat_id>/edit')
    def edit_threat(threat_id):
        from app.models import Threat
        threat = Threat.query.get_or_404(threat_id)
        return render_template('threats/form.html', threat=threat)
    
    @app.route('/threats/<int:threat_id>/edit-wizard')
    def edit_threat_wizard(threat_id):
        from app.models import Threat
        threat = Threat.query.get_or_404(threat_id)
        # Передаем ID угрозы как параметр в URL
        from flask import redirect
        return redirect(f'/threats/add-wizard/1?edit_threat_id={threat_id}')
    
    @app.route('/threats/assessment')
    def threat_assessment():
        from flask import redirect
        return redirect('/api/threats/assessment')
    
    @app.route('/threats/asset-mapping')
    def asset_threat_mapping():
        from flask import redirect
        return redirect('/api/threats/asset-mapping')
    
    @app.route('/threats/active-list')
    def threats_active_list():
        from flask import redirect
        return redirect('/api/threats/active-threats')
    
    @app.route('/threats/source-assessment')
    def threat_source_assessment():
        from flask import redirect
        return redirect('/api/threats/source-assessment')
    
    @app.route('/threats/probability-calculation')
    def threat_probability_calculation():
        from flask import redirect
        return redirect('/api/threats/probability-calculation')
    
    @app.route('/threats/probability-criteria')
    def threat_probability_criteria():
        from flask import redirect
        return redirect('/api/threats/probability-criteria')
    
    @app.route('/threats/probability-final-calculation')
    def threat_probability_final_calculation():
        from flask import redirect
        return redirect('/api/threats/probability-final-calculation')
    
    @app.route('/threats/probability-evaluation')
    def threat_probability_evaluation():
        from flask import redirect
        return redirect('/api/threats/probability-evaluation')
    
    @app.route('/threats/asset-probability-evaluation')
    def threat_asset_probability_evaluation():
        from flask import redirect
        return redirect('/api/threats/asset-probability-evaluation')
    
    @app.route('/threats/asset-probability-table')
    def threat_asset_probability_table():
        from flask import redirect
        return redirect('/api/threats/asset-probability-table')
    
    @app.route('/threats/select')
    def select_threats():
        return render_template('threats/select.html')
    
    @app.route('/vulnerabilities')
    def vulnerabilities_list():
        return render_template('vulnerabilities/list.html')
    
    @app.route('/vulnerabilities/create')
    def create_vulnerability():
        return render_template('vulnerabilities/form.html')
    
    @app.route('/vulnerabilities/<vulnerability_id>/edit')
    def edit_vulnerability(vulnerability_id):
        from app.models import Vulnerability
        vulnerability = Vulnerability.query.get_or_404(vulnerability_id)
        return render_template('vulnerabilities/form.html', vulnerability=vulnerability)

    @app.route('/vulnerabilities/identify')
    def identify_vulnerabilities():
        return render_template('vulnerabilities/identify.html')

    @app.route('/vulnerabilities/step2')
    def vulnerability_step2():
        return render_template('vulnerabilities/step2.html')

    @app.route('/vulnerabilities/step3')
    def vulnerability_step3():
        return render_template('vulnerabilities/step3.html')

    @app.route('/vulnerabilities/create-scale')
    def create_vulnerability_scale():
        return render_template('vulnerabilities/create_scale.html')

    @app.route('/vulnerabilities/assess')
    def assess_vulnerabilities():
        return render_template('vulnerabilities/assess.html')
    
    @app.route('/incidents')
    def incidents_list():
        return render_template('incidents/list.html')
    
    @app.route('/incidents/create')
    def create_incident():
        return render_template('incidents/form.html')
    
    @app.route('/incidents/<int:incident_id>/edit')
    def edit_incident(incident_id):
        from app.models import Incident
        incident = Incident.query.get_or_404(incident_id)
        return render_template('incidents/form.html', incident=incident)
    
    @app.route('/incidents/<int:incident_id>/tables')
    def incident_tables(incident_id):
        from app.models import Incident, Asset, Threat, Vulnerability
        incident = Incident.query.get_or_404(incident_id)
        
        # Получаем связанные данные
        asset = Asset.query.get(incident.asset_id)
        threat = Threat.query.get(incident.threat_id)
        vulnerability = Vulnerability.query.get(incident.vulnerability_id)
        
        # Получаем все инциденты для формирования таблиц
        incidents = Incident.query.all()
        
        return render_template('incidents/tables.html',
                             incident=incident,
                             asset=asset,
                             threat=threat,
                             vulnerability=vulnerability,
                             incidents=incidents)
    
    @app.route('/incidents/<int:incident_id>/edit-consequences')
    def edit_incident_consequences(incident_id):
        from app.models import Incident, Asset, Threat, Vulnerability
        incident = Incident.query.get_or_404(incident_id)
        
        # Получаем все связанные инциденты (созданные из одного запроса)
        related_incidents = Incident.query.filter_by(
            asset_id=incident.asset_id,
            threat_id=incident.threat_id,
            vulnerability_id=incident.vulnerability_id
        ).all()
        
        return render_template('incidents/edit_consequences.html',
                             incident=incident,
                             related_incidents=related_incidents)
    
    @app.route('/incidents/summary-tables')
    def incidents_summary_tables():
        from app.models import Incident
        incidents = Incident.query.all()
        return render_template('incidents/summary_tables.html', incidents=incidents)
    
    @app.route('/risks')
    def risks_list():
        return render_template('risks/list.html')
    
    @app.route('/risks/assessment')
    def risk_assessment():
        return render_template('risks/assessment.html')
    
    @app.route('/risks/create')
    def create_risk():
        return render_template('risks/form.html')
    
    @app.route('/risks/<int:risk_id>/edit')
    def edit_risk(risk_id):
        from app.models import Risk
        risk = Risk.query.get_or_404(risk_id)
        return render_template('risks/form.html', risk=risk)
    
    @app.route('/treatments')
    def treatments_list():
        return render_template('treatments/list.html')
    
    @app.route('/treatments/create')
    def create_treatment():
        return render_template('treatments/form.html')
    
    @app.route('/treatments/<int:treatment_id>/edit')
    def edit_treatment(treatment_id):
        from app.models import RiskTreatmentPlan
        treatment = RiskTreatmentPlan.query.get_or_404(treatment_id)
        return render_template('treatments/form.html', treatment=treatment)
    
    @app.route('/generate-report')
    def generate_report():
        from app.models import Context
        contexts = Context.query.all()
        return render_template('reports/generate.html', contexts=contexts)
    
    return app
