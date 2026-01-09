from app import create_app
from app import db
from app.models import ImpactCriterion
from app.utils.import_utils import load_default_threats_and_vulnerabilities

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


def create_app_with_db():
    app = create_app()
    
    with app.app_context():
        db.create_all()
        # Загружаем угрозы и уязвимости из файлов при запуске
        load_default_threats_and_vulnerabilities()
        # Создаем дефолтные критерии влияния
        create_default_impact_criteria()
    
    return app

app = create_app_with_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)