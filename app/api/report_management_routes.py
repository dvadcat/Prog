from flask import Blueprint, request, jsonify, send_file
from app.models import Report, Context
from app import db
import os
import json
from datetime import datetime

bp = Blueprint('report_management', __name__, url_prefix='/api/reports')

@bp.route('/', methods=['GET'])
def get_reports():
    """Получение списка всех отчетов"""
    try:
        reports = Report.query.all()
        return jsonify([report.to_dict() for report in reports])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:report_id>', methods=['GET'])
def get_report(report_id):
    """Получение конкретного отчета"""
    try:
        report = Report.query.get_or_404(report_id)
        return jsonify(report.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@bp.route('/<int:report_id>/download', methods=['GET'])
def download_report(report_id):
    """Скачивание отчета"""
    try:
        report = Report.query.get_or_404(report_id)
        if not os.path.exists(report.file_path):
            return jsonify({'error': 'Файл отчета не найден'}), 404
        
        return send_file(
            report.file_path, 
            as_attachment=True, 
            download_name=os.path.basename(report.file_path),
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@bp.route('/<int:report_id>', methods=['DELETE'])
def delete_report(report_id):
    """Удаление отчета"""
    try:
        report = Report.query.get_or_404(report_id)
        
        # Удаляем файл с диска
        if os.path.exists(report.file_path):
            os.remove(report.file_path)
        
        # Удаляем запись из БД
        db.session.delete(report)
        db.session.commit()
        
        return jsonify({'message': 'Отчет успешно удален'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/save', methods=['POST'])
def save_report():
    """Сохранение нового отчета"""
    try:
        data = request.get_json()
        
        # Создаем директорию для отчетов если её нет
        reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        # Генерируем имя файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{timestamp}.pdf"
        file_path = os.path.join(reports_dir, filename)
        
        # Создаем запись в БД
        report = Report(
            name=data.get('name', f'Отчет {timestamp}'),
            context_id=data.get('context_id'),
            file_path=file_path,
            file_size=data.get('file_size'),
            selected_data=json.dumps(data.get('selected_data', {}))
        )
        
        db.session.add(report)
        db.session.commit()
        
        return jsonify({
            'message': 'Отчет сохранен',
            'report_id': report.id,
            'report': report.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:report_id>', methods=['PUT'])
def update_report(report_id):
    """Обновление отчета"""
    try:
        report = Report.query.get_or_404(report_id)
        data = request.get_json()
        
        # Обновляем данные
        if 'name' in data:
            report.name = data['name']
        if 'context_id' in data:
            report.context_id = data['context_id']
        if 'selected_data' in data:
            report.selected_data = json.dumps(data['selected_data'])
        if 'file_size' in data:
            report.file_size = data['file_size']
        
        report.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Отчет обновлен',
            'report': report.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500