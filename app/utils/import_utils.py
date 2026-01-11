import pandas as pd
from app.models import Threat, Vulnerability
from app import db
import os

def import_threats_from_xlsx(file_path):
    """
    Импорт угроз из файла thrlist.xlsx (БДУ ФСТЭК)
    """
    try:
        # Чтение данных из Excel файла
        df = pd.read_excel(file_path)
        
        # Переименовываем столбцы для удобства работы
        column_mapping = {
            'Идентификатор УБИ': 'bdu_id',
            'Наименование УБИ': 'name',
            'Описание': 'description',
            'Источник угрозы (характеристика и потенциал нарушителя)': 'source',
            'Объект воздействия': 'target_object',
            'Нарушение конфиденциальности': 'confidentiality_violation',
            'Нарушение целостности': 'integrity_violation',
            'Нарушение доступности': 'availability_violation',
            'Дата включения угрозы в БнД УБИ': 'published_at',
            'Дата последнего изменения данных': 'updated_at'
        }
        
        # Переименовываем столбцы в DataFrame
        df.rename(columns=column_mapping, inplace=True)
        
        imported_count = 0
        
        for index, row in df.iterrows():
            # Проверяем, существует ли уже угроза с таким идентификатором УБИ
            existing_threat = Threat.query.filter_by(bdu_id=row.get('bdu_id')).first()
            
            if not existing_threat:
                threat = Threat(
                    bdu_id=row.get('bdu_id'),
                    name=row.get('name', ''),
                    description=row.get('description', ''),
                    source=row.get('source', ''),
                    target_object=row.get('target_object', ''),
                    confidentiality_violation=int(row.get('confidentiality_violation', 0)),
                    integrity_violation=int(row.get('integrity_violation', 0)),
                    availability_violation=int(row.get('availability_violation', 0)),
                    published_at=row.get('published_at'),
                    updated_at=row.get('updated_at'),
                    imported_from_bdu=True
                )
                
                db.session.add(threat)
                imported_count += 1
        
        db.session.commit()
        return imported_count
    
    except Exception as e:
        db.session.rollback()
        raise e

def import_vulnerabilities_from_xlsx(file_path):
    """
    Импорт уязвимостей из файла vullist.xlsx (БДУ ФСТЭК)
    """
    try:
        # Чтение данных из Excel файла
        df = pd.read_excel(file_path)
        
        imported_count = 0
        
        for index, row in df.iterrows():
            # Проверяем, существует ли уже уязвимость с таким ID
            existing_vulnerability = Vulnerability.query.filter_by(id=row.get('id', '')).first()
            
            if not existing_vulnerability:
                vulnerability = Vulnerability(
                    id=row.get('id', ''),
                    name=row.get('name', ''),
                    description=row.get('description', ''),
                    software_name=row.get('software_name', ''),
                    software_version=row.get('software_version', ''),
                    vendor=row.get('vendor', ''),
                    platform=row.get('platform', ''),
                    discovered_at=row.get('discovered_at'),
                    level=row.get('level', ''),
                    exploit_available=bool(row.get('exploit_available', False)),
                    fix_info=row.get('fix_info', ''),
                    cve=row.get('cve', ''),
                    cwe=row.get('cwe', ''),
                    cvss_score=row.get('cvss_score'),
                    imported_from_bdu=True
                )
                
                db.session.add(vulnerability)
                imported_count += 1
        
        db.session.commit()
        return imported_count
    
    except Exception as e:
        db.session.rollback()
        raise e

def load_default_threats_and_vulnerabilities():
    """
    Загрузка угроз и уязвимостей из файлов в директории data/
    """
    base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    threats_file = os.path.join(base_path, 'thrlist.xlsx')
    vulnerabilities_file = os.path.join(base_path, 'vullist.xlsx')
    
    imported_threats = 0
    imported_vulnerabilities = 0
    
    if os.path.exists(threats_file):
        imported_threats = import_threats_from_xlsx(threats_file)
    
    if os.path.exists(vulnerabilities_file):
        imported_vulnerabilities = import_vulnerabilities_from_xlsx(vulnerabilities_file)
    
    return imported_threats, imported_vulnerabilities