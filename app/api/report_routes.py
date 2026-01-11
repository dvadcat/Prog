from flask import Blueprint, request, send_file, jsonify
from app.utils.report_utils import generate_combined_pdf_report
from app.models import Report, Context
from app import db
import tempfile
import os
import json
from datetime import datetime

bp = Blueprint('reports', __name__, url_prefix='/api/reports')


@bp.route('/combined/pdf', methods=['POST'])
def download_combined_pdf_report():
    """
    Скачивание комбинированного PDF отчета с выбранными модулями
    """
    try:
        # Получаем данные из формы
        context_id = request.form.get('context_id')
        modules = request.form.getlist('modules[]')

        if not modules:
            return "Не выбраны модули для отчета", 400

        # Генерируем комбинированный отчет
        pdf_buffer = generate_combined_pdf_report(context_id, modules)
        
        # Создаем директорию для отчетов если её нет
        reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        # Генерируем имя файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"combined_report_{timestamp}.pdf"
        file_path = os.path.join(reports_dir, filename)
        
        # Сохраняем файл на диск
        with open(file_path, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        # Получаем размер файла
        file_size = os.path.getsize(file_path)
        
        # Создаем запись в БД
        report_name = f"Комбинированный отчет от {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        report = Report(
            name=report_name,
            context_id=int(context_id) if context_id else None,
            file_path=file_path,
            file_size=file_size,
            selected_data=json.dumps({'modules': modules})
        )
        
        db.session.add(report)
        db.session.commit()
        
        # Отправляем файл для скачивания
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        db.session.rollback()
        return str(e), 400
