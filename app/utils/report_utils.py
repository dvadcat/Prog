from flask import send_file, make_response
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, KeepTogether, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from app import db
from app.models import Context
from app.models import Threat, Vulnerability, Incident, Risk, RiskTreatmentPlan
from app.models import AssetSecurityPropertyImpact, ImpactCriterion
from app.models import AssetValueResult, ThreatAssessment, AssetThreat
from app.models import AssetVulnerability, VulnerabilityAssessment
from app.models.asset_dependency import AssetDependency
# Импорт Asset делаем отдельно для избежания проблем с циклическими импортами
from app.models.asset import Asset
from datetime import datetime

# Ширина страницы A4 = 8.27 дюймов, отступы по 0.5-1 дюйм с каждой стороны
# Полезная ширина для таблиц ~6.5-7 дюймов
PAGE_WIDTH = 6.5 * inch  # Полезная ширина страницы


def add_titled_table(elements, title, table, styles, spacer_after=12):
    """Добавляет заголовок и таблицу вместе, чтобы они не разрывались (для небольших таблиц)"""
    title_para = Paragraph(title, styles['Title'])
    elements.append(KeepTogether([title_para, Spacer(1, 6), table]))
    elements.append(Spacer(1, spacer_after))


def add_titled_table_smart(elements, title, table, styles, spacer_after=12, max_rows_for_keep=8):
    """
    Умное добавление заголовка и таблицы:
    - Маленькие таблицы (до max_rows_for_keep строк) - KeepTogether
    - Большие таблицы - только заголовок с первыми строками вместе
    """
    title_para = Paragraph(title, styles['Title'])
    
    # Проверяем количество строк в таблице
    try:
        row_count = len(table._cellvalues) if hasattr(table, '_cellvalues') else 0
    except:
        row_count = 0
    
    if row_count <= max_rows_for_keep:
        # Маленькая таблица - держим вместе
        elements.append(KeepTogether([title_para, Spacer(1, 6), table]))
    else:
        # Большая таблица - только заголовок не отрываем
        elements.append(KeepTogether([title_para, Spacer(1, 6)]))
        elements.append(table)
    
    elements.append(Spacer(1, spacer_after))


def add_titled_content(elements, title, content_list, styles, spacer_after=12):
    """Добавляет заголовок и контент вместе"""
    all_content = [Paragraph(title, styles['Title']), Spacer(1, 6)]
    all_content.extend(content_list)
    elements.append(KeepTogether(all_content))
    elements.append(Spacer(1, spacer_after))


# Регистрация шрифта с поддержкой кириллицы
def register_cyrillic_font():
    try:
        import os
        import platform
        
        if platform.system() == "Windows":
            regular_font_path = 'C:/Windows/Fonts/arial.ttf'
            bold_font_path = 'C:/Windows/Fonts/arialbd.ttf'
            
            if os.path.exists(regular_font_path):
                pdfmetrics.registerFont(TTFont('CyrillicFont', regular_font_path))
                if os.path.exists(bold_font_path):
                    pdfmetrics.registerFont(TTFont('CyrillicFont-Bold', bold_font_path))
                return 'CyrillicFont'
        else:
            regular_font_paths = [
                '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
            ]
            bold_font_paths = [
                '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
            ]
            
            for regular_path in regular_font_paths:
                if os.path.exists(regular_path):
                    pdfmetrics.registerFont(TTFont('CyrillicFont', regular_path))
                    for bold_path in bold_font_paths:
                        if os.path.exists(bold_path):
                            pdfmetrics.registerFont(TTFont('CyrillicFont-Bold', bold_path))
                            break
                    return 'CyrillicFont'
        
        return 'Helvetica'
    except:
        return 'Helvetica'

CYRILLIC_FONT = register_cyrillic_font()

def create_cyrillic_style_sheet():
    """Создание стилей с поддержкой кириллицы"""
    styles = getSampleStyleSheet()
    
    try:
        from reportlab.pdfbase.pdfmetrics import getFont
        getFont(CYRILLIC_FONT)
        font_name = CYRILLIC_FONT
    except:
        font_name = 'Helvetica'
    
    title_style = ParagraphStyle(
        'CyrillicTitle',
        parent=styles['Title'],
        fontName=font_name,
        fontSize=14,
        spaceAfter=10
    )
    
    normal_style = ParagraphStyle(
        'CyrillicNormal',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=9,
        leading=11,
        wordWrap='LTR',
        allowWidows=1,
        allowOrphans=1
    )
    
    table_style = ParagraphStyle(
        'CyrillicTable',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=7,
        leading=9,
        wordWrap='LTR',
        allowWidows=1,
        allowOrphans=1,
        leftIndent=2,
        rightIndent=2,
        spaceAfter=0,
        spaceBefore=0
    )
    
    return {
        'Title': title_style,
        'Normal': normal_style,
        'Table': table_style
    }

def wrap_text(text, max_length=30):
    """Разбивка текста на строки указанной длины"""
    if not isinstance(text, str) or len(text) <= max_length:
        return text
    
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        if len(current_line + " " + word) <= max_length:
            current_line += " " + word if current_line else word
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    return "<br/>".join(lines)

def wrap_cell_text(cell, styles, max_length=30):
    """Обертка текста ячейки в Paragraph для переноса"""
    if isinstance(cell, Paragraph):
        return cell
    if isinstance(cell, str):
        return Paragraph(wrap_text(cell, max_length), styles['Table'])
    return cell

def create_table_data_with_wrapping(data, styles, max_length=30):
    """Создание данных таблицы с переносом текста для всех ячеек"""
    wrapped_data = []
    for row in data:
        wrapped_row = []
        for cell in row:
            wrapped_row.append(wrap_cell_text(cell, styles, max_length))
        wrapped_data.append(wrapped_row)
    return wrapped_data

def calculate_column_widths(num_columns, total_width=None, min_width=0.5*inch, max_width=2*inch):
    """
    Расчет ширины колонок с учетом общего количества и общей ширины
    """
    if total_width is None:
        total_width = PAGE_WIDTH
    
    if num_columns <= 0:
        return []
    
    # Равномерное распределение с учетом ограничений
    base_width = total_width / num_columns
    
    # Ограничиваем минимальную и максимальную ширину
    if base_width < min_width:
        base_width = min_width
    elif base_width > max_width:
        base_width = max_width
    
    return [base_width] * num_columns

def create_standard_table(data, styles, col_widths=None, num_columns=None):
    """
    Создание стандартной таблицы с авто-шириной колонок
    """
    if col_widths is None:
        if num_columns is None:
            num_columns = len(data[0]) if data else 0
        col_widths = calculate_column_widths(num_columns)
    
    # Оборачиваем все ячейки в Paragraph
    wrapped_data = create_table_data_with_wrapping(data, styles)
    
    table = Table(wrapped_data, colWidths=col_widths)
    table.setStyle(create_table_style())
    return table

def create_table_style():
    """Создание стиля таблицы с поддержкой кириллицы"""
    header_font = f'{CYRILLIC_FONT}-Bold' if CYRILLIC_FONT != 'Helvetica' else 'Helvetica-Bold'
    
    return TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), header_font),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('FONTNAME', (0, 1), (-1, -1), CYRILLIC_FONT),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 1), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
        ('SPLITLONGWORDS', (0, 0), (-1, -1), True),
        ('NOWRAP', (0, 0), (-1, -1), False)
    ])

def create_detailed_table_style():
    """Создание стиля подробной таблицы"""
    header_font = f'{CYRILLIC_FONT}-Bold' if CYRILLIC_FONT != 'Helvetica' else 'Helvetica-Bold'
    
    return TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), header_font),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('FONTNAME', (0, 1), (-1, -1), CYRILLIC_FONT),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ])

def generate_combined_pdf_report(context_id, modules):
    """
    Генерация комбинированного PDF отчета с выбранными модулями
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=0.5*inch, rightMargin=0.5*inch, topMargin=0.75*inch, bottomMargin=0.75*inch)
    elements = []
    styles = create_cyrillic_style_sheet()
    
    title = "Отчёт по оценке рисков информационной безопасности"
    elements.append(Paragraph(title, styles['Title']))
    elements.append(Spacer(1, 10))
    
    current_date = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    elements.append(Paragraph(f"Дата формирования: {current_date}", styles['Normal']))
    elements.append(Spacer(1, 10))
    
    if context_id:
        context = Context.query.get(context_id)
        if context:
            elements.append(Paragraph(f"Название объекта: {context.name}", styles['Normal']))
            elements.append(Spacer(1, 6))
    
    module_names = {
        'assets': 'Активы',
        'threats': 'Угрозы',
        'vulnerabilities': 'Уязвимости',
        'incidents': 'Инциденты',
        'risks': 'Риски'
    }
    
    elements.append(Paragraph("Включенные модули:", styles['Normal']))
    for module in modules:
        if module in module_names:
            elements.append(Paragraph(f"• {module_names[module]}", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    for module in modules:
        if module == 'assets':
            elements.append(Paragraph("1. АКТИВЫ", styles['Title']))
            elements.append(Spacer(1, 8))
            
            if context_id:
                context = Context.query.get(context_id)
                if context:
                    elements.append(Paragraph("Информация об области управления рисками и критериев риска:", styles['Title']))
                    elements.append(Spacer(1, 6))
                    
                    elements.append(Paragraph(f"Название объекта: {context.name}", styles['Normal']))
                    elements.append(Paragraph(f"ФИО ответственного: {context.owner_name or ''}", styles['Normal']))
                    elements.append(Paragraph(f"Описание объекта: {context.description or ''}", styles['Normal']))
                    
                    if context.selected_impact_criteria:
                        try:
                            import json
                            criteria = json.loads(context.selected_impact_criteria)
                            elements.append(Paragraph("Критерии влияния риска:", styles['Normal']))
                            for crit in criteria:
                                elements.append(Paragraph(f"• {crit}", styles['Normal']))
                        except:
                            pass
                    
                    # Шкалы ущерба (до критериев оценивания рисков)
                    if context.damage_scales:
                        try:
                            import json
                            scales = json.loads(context.damage_scales)
                            elements.append(Paragraph("Шкалы ущерба:", styles['Normal']))
                            for crit, scale in scales.items():
                                elements.append(Paragraph(f"Критерий: {crit}", styles['Normal']))
                                elements.append(Paragraph(f"Минимальная: {scale.get('minimal', '')}", styles['Normal']))
                                elements.append(Paragraph(f"Средняя: {scale.get('medium', '')}", styles['Normal']))
                                elements.append(Paragraph(f"Высокая: {scale.get('high', '')}", styles['Normal']))
                        except:
                            pass
                    
                    if context.risk_evaluation_criteria:
                        try:
                            import json
                            risk_crit = json.loads(context.risk_evaluation_criteria)
                            elements.append(Paragraph("Критерии оценивания рисков ИБ:", styles['Normal']))
                            elements.append(Paragraph(f"Низкий уровень: {risk_crit.get('low', '')}", styles['Normal']))
                            elements.append(Paragraph(f"Средний уровень: {risk_crit.get('medium', '')}", styles['Normal']))
                            elements.append(Paragraph(f"Высокий уровень: {risk_crit.get('high', '')}", styles['Normal']))
                        except:
                            pass
                    
                    # Критерии принятия риска
                    if context.risk_acceptance_criteria:
                        try:
                            import json
                            acceptance_crit = json.loads(context.risk_acceptance_criteria)
                            elements.append(Paragraph("Критерии принятия риска:", styles['Normal']))
                            elements.append(Paragraph(f"Низкий уровень риска: {acceptance_crit.get('low', 'приемлемый')}", styles['Normal']))
                            elements.append(Paragraph(f"Средний уровень риска: {acceptance_crit.get('medium', 'приемлемый')}", styles['Normal']))
                            elements.append(Paragraph(f"Высокий уровень риска: {acceptance_crit.get('high', 'неприемлемый')}", styles['Normal']))
                        except:
                            pass
                    
                    elements.append(Spacer(1, 12))
            
            query = db.session.query(Asset).join(Context)
            if context_id:
                query = query.filter(Asset.context_id == context_id)
            
            assets = query.all()
            
            if assets:
                # Перечень активов
                elements.append(Paragraph("Перечень активов:", styles['Title']))
                elements.append(Spacer(1, 6))
                
                type_translations = {
                    'information': 'Информационный',
                    'software': 'Программный',
                    'hardware': 'Аппаратный',
                    'personnel': 'Персонал',
                    'facility': 'Объект недвижимости',
                    'network': 'Сетевой',
                    'data': 'Данные',
                    'service': 'Услуга'
                }
                
                asset_table_data = [
                    ['ID', 'Наименование', 'Тип', 'Свойства ИБ', 
                     'Ценность без зависимостей', 'Ценность с зависимостями', 'Стоимость', 'Дата создания']
                ]
                
                for asset in assets:
                    properties_text = ''
                    if asset.properties:
                        try:
                            import json
                            props = json.loads(asset.properties)
                            props_list = []
                            if props.get('confidentiality'): props_list.append('К')
                            if props.get('integrity'): props_list.append('Ц')
                            if props.get('availability'): props_list.append('Д')
                            properties_text = ','.join(props_list)
                        except:
                            properties_text = 'Ошибка'
                    
                    translated_type = type_translations.get(asset.type, asset.type)
                    cost_text = f"{asset.asset_cost} тыс.руб." if asset.asset_cost else '-'
                    created_at_text = asset.created_at.strftime('%d.%m.%Y') if asset.created_at else '-'
                    
                    asset_table_data.append([
                        str(asset.id),
                        asset.name,
                        translated_type,
                        properties_text,
                        str(asset.value_without_dependencies) if asset.value_without_dependencies else '-',
                        str(asset.dependency_value) if asset.dependency_value else '-',
                        cost_text,
                        created_at_text
                    ])
                
                asset_table = create_standard_table(asset_table_data, styles, num_columns=8)
                elements.append(asset_table)
                elements.append(Spacer(1, 12))
                
                # Шкала стоимости актива (после перечня активов)
                cost_scale_context = Context.query.filter(Context.asset_cost_scale.isnot(None)).first()
                if cost_scale_context and cost_scale_context.asset_cost_scale:
                    try:
                        import json
                        cost_scale = json.loads(cost_scale_context.asset_cost_scale)
                        
                        # Добавляем " руб." к значениям
                        low_val = cost_scale.get('low_value', '-')
                        med_val = cost_scale.get('medium_value', '-')
                        high_val = cost_scale.get('high_value', '-')
                        
                        if low_val and low_val != '-':
                            low_val = f"{low_val} руб."
                        if med_val and med_val != '-':
                            med_val = f"{med_val} руб."
                        if high_val and high_val != '-':
                            high_val = f"{high_val} руб."
                        
                        cost_scale_data = [
                            ['Стоимость актива', 'Диапазон'],
                            ['Низкая', low_val],
                            ['Средняя', med_val],
                            ['Высокая', high_val]
                        ]
                        cost_scale_table = create_standard_table(cost_scale_data, styles, num_columns=2)
                        
                        elements.append(KeepTogether([
                            Paragraph("Шкала стоимости актива:", styles['Title']),
                            Spacer(1, 6),
                            cost_scale_table
                        ]))
                        elements.append(Spacer(1, 12))
                    except:
                        pass
                
                # Основная таблица - свойства ИБ
                elements.append(Paragraph("Свойства информационной безопасности активов:", styles['Title']))
                elements.append(Spacer(1, 6))
                
                data = [['Название актива', 'Конфиденциальность', 'Целостность', 'Доступность']]
                for asset in assets:
                    try:
                        import json
                        props = json.loads(asset.properties) if asset.properties else {}
                        conf = 'Да' if props.get('confidentiality') else 'Нет'
                        integ = 'Да' if props.get('integrity') else 'Нет'
                        avail = 'Да' if props.get('availability') else 'Нет'
                    except:
                        conf = integ = avail = 'Нет'
                    
                    data.append([asset.name, conf, integ, avail])
                
                main_table = create_standard_table(data, styles, num_columns=4)
                elements.append(main_table)
                elements.append(Spacer(1, 12))
                
                # Ценность активов относительно нарушения свойств ИБ
                elements.append(Paragraph("Ценность активов относительно нарушения свойств ИБ", styles['Title']))
                elements.append(Spacer(1, 6))
                
                impact_criteria = []
                impact_criteria_dict = {}
                
                if assets:
                    asset_ids = [a.id for a in assets]
                    impacts = AssetSecurityPropertyImpact.query.filter(
                        AssetSecurityPropertyImpact.asset_id.in_(asset_ids),
                        AssetSecurityPropertyImpact.impact_criterion_id.isnot(None)
                    ).all()
                    
                    criterion_ids = set()
                    for impact in impacts:
                        if impact.impact_criterion_id:
                            criterion_ids.add(impact.impact_criterion_id)
                    
                    if criterion_ids:
                        criteria = ImpactCriterion.query.filter(ImpactCriterion.id.in_(criterion_ids)).all()
                        for criterion in criteria:
                            impact_criteria_dict[criterion.id] = criterion.name
                        
                        impact_criteria = [impact_criteria_dict[cid] for cid in sorted(criterion_ids) if cid in impact_criteria_dict]
                
                header_row = ['Актив', 'Свойства ИБ'] + impact_criteria + ['Ценность актива']
                table8_data = [header_row]
                
                criterion_id_by_name = {name: cid for cid, name in impact_criteria_dict.items()}
                
                # Порядок значений для определения максимального
                VALUE_ORDER = {'Н': 1, 'С': 2, 'В': 3}
                
                for asset in assets:
                    security_properties = ['confidentiality', 'integrity', 'availability']
                    security_property_names = ['Конфиденциальность', 'Целостность', 'Доступность']
                    
                    # Сначала собираем все значения для этого актива
                    asset_impact_values = []
                    
                    for prop in security_properties:
                        for criterion_name in impact_criteria:
                            criterion_id = criterion_id_by_name.get(criterion_name)
                            if criterion_id:
                                impact_data = AssetSecurityPropertyImpact.query.filter_by(
                                    asset_id=asset.id,
                                    security_property=prop,
                                    impact_criterion_id=criterion_id
                                ).first()
                                impact_value = impact_data.impact_value if impact_data else '-'
                                if impact_value and impact_value not in ['', '-']:
                                    asset_impact_values.append(impact_value)
                    #print(asset_impact_values)
                    # Определяем максимальное значение
                    max_value = '-'
                    if asset_impact_values:
                        # Сортируем по порядку и берем максимальное
                        sorted_values = sorted(asset_impact_values, key=lambda x: VALUE_ORDER.get(x, 0), reverse=True)
                        print(sorted_values)
                        max_value = sorted_values[0]
                    
                    # Теперь создаем строки таблицы
                    for i, (prop, prop_name) in enumerate(zip(security_properties, security_property_names)):
                        row = [asset.name, prop_name]
                        
                        for criterion_name in impact_criteria:
                            criterion_id = criterion_id_by_name.get(criterion_name)
                            if criterion_id:
                                impact_data = AssetSecurityPropertyImpact.query.filter_by(
                                    asset_id=asset.id,
                                    security_property=prop,
                                    impact_criterion_id=criterion_id
                                ).first()
                                impact_value = impact_data.impact_value if impact_data else '-'
                            else:
                                impact_value = '-'
                            row.append(impact_value)
                        
                        # Максимальное значение пишем только в первой строке для этого актива
                        if i == 0:
                            row.append(max_value)
                        else:
                            row.append('')
                        
                        table8_data.append(row)
                
                table8 = create_standard_table(table8_data, styles, num_columns=len(header_row))
                elements.append(table8)
                elements.append(Spacer(1, 12))
                
                # Зависимость активов
                elements.append(Paragraph("Зависимость активов", styles['Title']))
                elements.append(Spacer(1, 6))
                
                if len(assets) > 0:
                    asset_ids = [a.id for a in assets]
                    dependencies = AssetDependency.query.filter(
                        AssetDependency.asset_id.in_(asset_ids),
                        AssetDependency.depends_on_asset_id.in_(asset_ids)
                    ).all()
                    
                    dep_dict = {}
                    for dep in dependencies:
                        if dep.asset_id not in dep_dict:
                            dep_dict[dep.asset_id] = set()
                        dep_dict[dep.asset_id].add(dep.depends_on_asset_id)
                    
                    dep_table_data = [['Актив'] + [a.name for a in assets]]
                    
                    for asset in assets:
                        row = [asset.name]
                        for other_asset in assets:
                            if asset.id == other_asset.id:
                                row.append('')
                            elif asset.id in dep_dict and other_asset.id in dep_dict[asset.id]:
                                row.append('+')
                            else:
                                row.append('-')
                        dep_table_data.append(row)
                    
                    dep_table = create_standard_table(dep_table_data, styles, num_columns=len(dep_table_data[0]))
                    elements.append(dep_table)
                    elements.append(Spacer(1, 6))
                    elements.append(Paragraph("Примечание: '+' - актив зависит от указанного актива, '-' - зависимости нет", styles['Normal']))
                else:
                    elements.append(Paragraph("Нет данных о зависимостях активов", styles['Normal']))
            else:
                elements.append(Paragraph("Данные об активах отсутствуют", styles['Normal']))
            
            elements.append(Spacer(1, 12))
            
        elif module == 'threats':
            elements.append(PageBreak())
            elements.append(Paragraph("2. УГРОЗЫ", styles['Title']))
            elements.append(Spacer(1, 8))
            
            # Только актуальные угрозы
            threats = Threat.query.filter_by(is_relevant=True).all()
            
            if threats:
                for threat in threats:
                    # Заголовок угрозы с таблицей вместе
                    threat_data = [
                        ['Параметр', 'Значение'],
                        ['Наименование', threat.name],
                        ['Описание', threat.description or ''],
                        ['Источник', threat.source or ''],
                        ['Объект воздействия', threat.target_object or ''],
                        ['Нарушение конфиденциальности', 'Да' if threat.confidentiality_violation else 'Нет'],
                        ['Нарушение целостности', 'Да' if threat.integrity_violation else 'Нет'],
                        ['Нарушение доступности', 'Да' if threat.availability_violation else 'Нет'],
                        ['Актуальность', 'Да' if threat.is_relevant else 'Нет']
                    ]
                    
                    wrapped_threat_data = create_table_data_with_wrapping(threat_data, styles, max_length=60)
                    threat_table = Table(wrapped_threat_data, colWidths=[2*inch, 4*inch])
                    threat_table.setStyle(create_detailed_table_style())
                    
                    elements.append(KeepTogether([
                        Paragraph(f"Угроза: {threat.name}", styles['Title']),
                        Spacer(1, 6),
                        threat_table
                    ]))
                    elements.append(Spacer(1, 12))
                    
                    if threat.is_relevant:
                        import json
                        properties = json.loads(threat.step5)

                        threat_props_data = [
                            ['Информационные активы', ''],
                            ['К (Конфиденциальность)', '+' if properties.get('info_conf') else '-'],
                            ['Ц (Целостность)',       '+' if properties.get('info_int') else '-'],
                            ['Д (Доступность)',       '+' if properties.get('info_av') else '-'],
                            ['Аппаратные средства',   ''],
                            ['К (Конфиденциальность)', '+' if properties.get('hw_conf') else '-'],
                            ['Ц (Целостность)',       '+' if properties.get('hw_int') else '-'],
                            ['Д (Доступность)',       '+' if properties.get('hw_av') else '-'],
                            ['Программные средства',  ''],
                            ['К (Конфиденциальность)', '+' if properties.get('sw_conf') else '-'],
                            ['Ц (Целостность)',       '+' if properties.get('sw_int') else '-'],
                            ['Д (Доступность)',       '+' if properties.get('sw_av') else '-']
                        ]
                        wrapped_props_data = create_table_data_with_wrapping(threat_props_data, styles, max_length=60)
                        threat_props_table = Table(wrapped_props_data, colWidths=[2*inch, 4*inch])
                        threat_props_table.setStyle(create_detailed_table_style())
                        elements.append(threat_props_table)
                        elements.append(Spacer(1, 12))

                    # Оценка признака "Источник угрозы ИБ"
                    static_table_data = [
                        ['Признак', '1 балл', '2 балла', '3 балла', '4 балла'],
                        ['Мотивация ИУ', 'отсутствует', '', '', 'присутствует'],
                        ['Квалификация ИУ', 'отсутствие знаний и навыков', 
                         'знания на уровне пользователя',
                         'владение языками программирования, знания администрирования',
                         'знания на уровне разработчика'],
                        ['Ресурсы ИУ', 'ресурсы физ. лица',
                         'ресурсы группы лиц',
                         'ресурсы организации',
                         'поддержка на уровне гос-ва'],
                        ['Расположение ИУ', 'внешнее', 'внутреннее', '', 'внешнее и внутреннее']
                    ]
                    
                    wrapped_static_data = create_table_data_with_wrapping(static_table_data, styles, max_length=35)
                    static_table = Table(wrapped_static_data)
                    static_table.setStyle(create_table_style())
                    
                    elements.append(KeepTogether([
                        Paragraph("Оценка признака 'Источник угрозы ИБ'", styles['Title']),
                        Spacer(1, 6),
                        static_table
                    ]))
                    elements.append(Spacer(1, 6))
                    
                    if threat.source_assessment:
                        try:
                            import json
                            source_data = json.loads(threat.source_assessment)
                            elements.append(Paragraph(f"Оценка: {source_data.get('assessment', 'Нет данных')}", styles['Normal']))
                            
                            if 'scores' in source_data:
                                scores = source_data['scores']
                                user_scores_data = [
                                    ['Признак', 'Оценка'],
                                    ['Мотивация ИУ', str(scores.get('motivation', 'Не указано'))],
                                    ['Квалификация ИУ', str(scores.get('qualification', 'Не указано'))],
                                    ['Ресурсы ИУ', str(scores.get('resources', 'Не указано'))],
                                    ['Расположение ИУ', str(scores.get('location', 'Не указано'))]
                                ]
                                
                                user_scores_table = Table(create_table_data_with_wrapping(user_scores_data, styles))
                                user_scores_table.setStyle(create_table_style())
                                elements.append(user_scores_table)
                        except:
                            elements.append(Paragraph("Ошибка чтения данных оценки", styles['Normal']))
                    
                    elements.append(Spacer(1, 12))
                    
                    # Критерии оценки вероятности реализации угрозы
                    criteria_table_data = [
                        ['Признак', '1 балл', '2 балла', '3 балла', '4 балла'],
                        ['Продолжительность реализации', 'кратковременная', 'непрерывная непродолжительная', '', 'длительная непрерывная'],
                        ['Возможность обнаружения', 'легко', 'трудно', 'очень трудно', 'невозможно'],
                        ['Возможность нейтрализации', 'легко', 'трудно', 'очень трудно', 'невозможно'],
                        ['Источник угрозы ИБ', 'I = 1/4', '1/4 < I ≤ 1/2', '1/2 < I ≤ 3/4', '3/4 < I ≤ 1']
                    ]
                    
                    wrapped_criteria_data = create_table_data_with_wrapping(criteria_table_data, styles, max_length=35)
                    criteria_table = Table(wrapped_criteria_data)
                    criteria_table.setStyle(create_table_style())
                    
                    values_table_data = [
                        ['Качественное значение', 'Количественное значение'],
                        ['Минимальная', '[0,25; 0,4]'],
                        ['Средняя', '[0,4; 0,7]'],
                        ['Высокая', '[0,7; 1]']
                    ]
                    
                    values_table = Table(create_table_data_with_wrapping(values_table_data, styles))
                    values_table.setStyle(create_table_style())
                    
                    # Объединяем заголовок и обе таблицы вместе
                    elements.append(KeepTogether([
                        Paragraph("Критерии оценки вероятности реализации угрозы", styles['Title']),
                        Spacer(1, 6),
                        criteria_table,
                        Spacer(1, 6),
                        values_table
                    ]))
                    elements.append(Spacer(1, 12))
                    
                    if threat.probability_assessment:
                        try:
                            import json
                            prob_data = json.loads(threat.probability_assessment)
                            elements.append(Paragraph(f"Оценка вероятности: {prob_data.get('assessment', 'Нет данных')}", styles['Normal']))
                            
                            if 'scores' in prob_data:
                                scores = prob_data['scores']
                                prob_scores_data = [
                                    ['Признак', 'Оценка'],
                                    ['Продолжительность', str(scores.get('duration', 'Не указано'))],
                                    ['Возможность обнаружения', str(scores.get('detectability', 'Не указано'))],
                                    ['Возможность нейтрализации', str(scores.get('neutralization', 'Не указано'))],
                                    ['Источник угрозы', str(scores.get('source', 'Не указано'))]
                                ]
                                
                                prob_scores_table = Table(create_table_data_with_wrapping(prob_scores_data, styles))
                                prob_scores_table.setStyle(create_table_style())
                                elements.append(prob_scores_table)
                        except:
                            elements.append(Paragraph("Ошибка чтения данных оценки вероятности", styles['Normal']))
                    
                    elements.append(Spacer(1, 12))
                
                # Итоговая таблица
                elements.append(Paragraph("Итог: Оценка вероятности реализации угроз для активов", styles['Title']))
                elements.append(Spacer(1, 6))
                
                threat_assessments = ThreatAssessment.query.all()
                all_assets = Asset.query.all()
                # Только актуальные угрозы
                all_threats = Threat.query.filter_by(is_relevant=True).all()
                
                assets_dict = {a.id: a for a in all_assets}
                threats_dict = {t.id: t for t in all_threats}
                
                valid_assessments = []
                for ta in threat_assessments:
                    asset = assets_dict.get(ta.asset_id)
                    threat_obj = threats_dict.get(ta.threat_id)
                    if asset and threat_obj:
                        valid_assessments.append(ta)
                
                if valid_assessments:
                    info_assets = {}
                    software_assets = {}
                    hardware_assets = {}
                    other_assets = {}
                    
                    for assessment in valid_assessments:
                        asset = assets_dict.get(assessment.asset_id)
                        threat_obj = threats_dict.get(assessment.threat_id)
                        
                        if not asset or not threat_obj:
                            continue
                        
                        if assessment.assessment is not None and assessment.assessment != '':
                            level = assessment.assessment
                        else:
                            level = get_assessment_level(assessment.score if assessment.score is not None else 0.5)
                        
                        table_row = [threat_obj.name, level]
                        
                        if asset.type == 'information':
                            if asset.id not in info_assets:
                                info_assets[asset.id] = {'asset': asset, 'threats': []}
                            info_assets[asset.id]['threats'].append(table_row)
                        elif asset.type == 'software':
                            if asset.id not in software_assets:
                                software_assets[asset.id] = {'asset': asset, 'threats': []}
                            software_assets[asset.id]['threats'].append(table_row)
                        elif asset.type == 'hardware':
                            if asset.id not in hardware_assets:
                                hardware_assets[asset.id] = {'asset': asset, 'threats': []}
                            hardware_assets[asset.id]['threats'].append(table_row)
                        else:
                            if asset.id not in other_assets:
                                other_assets[asset.id] = {'asset': asset, 'threats': []}
                            other_assets[asset.id]['threats'].append(table_row)
                    
                    final_table_data = []
                    
                    if info_assets:
                        final_table_data.append([Paragraph('<b>Информационные активы</b>', styles['Normal']), '', ''])
                        for asset_data in info_assets.values():
                            asset = asset_data['asset']
                            threats_list = asset_data['threats']
                            if threats_list:
                                final_table_data.append([
                                    asset.name,
                                    threats_list[0][0],
                                    threats_list[0][1]
                                ])
                                for threat_row in threats_list[1:]:
                                    final_table_data.append(['', threat_row[0], threat_row[1]])
                    
                    if software_assets:
                        final_table_data.append([Paragraph('<b>Программные средства</b>', styles['Normal']), '', ''])
                        for asset_data in software_assets.values():
                            asset = asset_data['asset']
                            threats_list = asset_data['threats']
                            if threats_list:
                                final_table_data.append([
                                    asset.name,
                                    threats_list[0][0],
                                    threats_list[0][1]
                                ])
                                for threat_row in threats_list[1:]:
                                    final_table_data.append(['', threat_row[0], threat_row[1]])
                    
                    if hardware_assets:
                        final_table_data.append([Paragraph('<b>Аппаратные средства</b>', styles['Normal']), '', ''])
                        for asset_data in hardware_assets.values():
                            asset = asset_data['asset']
                            threats_list = asset_data['threats']
                            if threats_list:
                                final_table_data.append([
                                    asset.name,
                                    threats_list[0][0],
                                    threats_list[0][1]
                                ])
                                for threat_row in threats_list[1:]:
                                    final_table_data.append(['', threat_row[0], threat_row[1]])
                    
                    if other_assets:
                        final_table_data.append([Paragraph('<b>Прочие активы</b>', styles['Normal']), '', ''])
                        for asset_data in other_assets.values():
                            asset = asset_data['asset']
                            threats_list = asset_data['threats']
                            if threats_list:
                                final_table_data.append([
                                    asset.name,
                                    threats_list[0][0],
                                    threats_list[0][1]
                                ])
                                for threat_row in threats_list[1:]:
                                    final_table_data.append(['', threat_row[0], threat_row[1]])
                    
                    if final_table_data:
                        header_row = [
                            Paragraph('<b>Актив</b>', styles['Normal']),
                            Paragraph('<b>Угроза</b>', styles['Normal']),
                            Paragraph('<b>Оценка</b>', styles['Normal'])
                        ]
                        final_table_data.insert(0, header_row)
                        
                        wrapped_final_data = create_table_data_with_wrapping(final_table_data, styles, max_length=35)
                        final_table = Table(wrapped_final_data, colWidths=[1.8*inch, 3*inch, 1.2*inch])
                        final_table.setStyle(create_table_style())
                        elements.append(final_table)
                    else:
                        elements.append(Paragraph("Нет данных для отображения", styles['Normal']))
                else:
                    elements.append(Paragraph("Данные для оценки вероятности отсутствуют", styles['Normal']))
            else:
                elements.append(Paragraph("Данные об угрозах отсутствуют", styles['Normal']))
            
            elements.append(Spacer(1, 12))
            
        elif module == 'vulnerabilities':
            elements.append(PageBreak())
            elements.append(Paragraph("3. УЯЗВИМОСТИ", styles['Title']))
            elements.append(Spacer(1, 8))
            
            # Список выявленных уязвимостей
            elements.append(Paragraph("Список выявленных уязвимостей", styles['Title']))
            elements.append(Spacer(1, 6))
            
            vulnerabilities = Vulnerability.query.all()
            
            if vulnerabilities:
                table_data = [['ID', 'Наименование', 'Описание']]
                for vuln in vulnerabilities:
                    description = vuln.description or ''
                    truncated_desc = description
                    table_data.append([
                        str(vuln.id),
                        vuln.name,
                        truncated_desc
                    ])
                
                vuln_table = create_standard_table(table_data, styles, num_columns=3)
                elements.append(vuln_table)
            else:
                elements.append(Paragraph("Уязвимости не выявлены", styles['Normal']))
            
            elements.append(Spacer(1, 12))
            
            # Качественная шкала оценки уязвимостей
            elements.append(Paragraph("Качественная шкала оценки уязвимостей", styles['Title']))
            elements.append(Spacer(1, 6))
            
            scale_data = []
            av_with_scale = AssetVulnerability.query.filter(AssetVulnerability.scale_json.isnot(None)).first()
            if av_with_scale and av_with_scale.scale_json:
                try:
                    import json
                    scale_data = json.loads(av_with_scale.scale_json)
                except:
                    scale_data = []
            
            if not scale_data:
                scale_data = [
                    {'name': 'Низкий', 'description': 'Уязвимость существует у актива в минимальной степени'},
                    {'name': 'Средний', 'description': 'Уязвимость существует у актива частично'},
                    {'name': 'Высокий', 'description': 'Уязвимость существует у актива в максимальной степени'}
                ]
            
            scale_table_data = [['Уровень', 'Описание']]
            for level in scale_data:
                scale_table_data.append([
                    level.get('name', ''),
                    level.get('description', '')
                ])
            
            scale_table = create_standard_table(scale_table_data, styles, num_columns=2)
            elements.append(scale_table)
            elements.append(Spacer(1, 12))
            
            # Оценка уязвимостей активов
            elements.append(Paragraph("Оценка уязвимостей активов", styles['Title']))
            elements.append(Spacer(1, 6))
            
            asset_vulns = AssetVulnerability.query.all()
            asset_vuln_map = {}
            vul_map = {}
            asset_map = {}
            
            if asset_vulns:
                for av in asset_vulns:
                    if av.vulnerability_id == 'scale_only' or av.vulnerability_id is None or av.asset_id is None:
                        continue
                    
                    asset = Asset.query.get(av.asset_id)
                    vulnerability = Vulnerability.query.get(av.vulnerability_id)
                    if not asset or not vulnerability:
                        continue
                    
                    asset_map[av.asset_id] = asset
                    vul_map[av.vulnerability_id] = vulnerability
                    
                    if av.asset_id not in asset_vuln_map:
                        asset_vuln_map[av.asset_id] = {}
                    
                    assessment_value = av.assessment or '-'
                    if av.scale_json:
                        try:
                            import json
                            scale_data = json.loads(av.scale_json)
                            if isinstance(scale_data, list) and len(scale_data) > 0:
                                assessment_value = scale_data[0].get('name', assessment_value)
                            elif isinstance(scale_data, dict):
                                assessment_value = scale_data.get('name', assessment_value)
                        except:
                            pass
                    
                    asset_vuln_map[av.asset_id][av.vulnerability_id] = assessment_value
            
            if asset_vuln_map:
                type_names = {
                    'information': 'Информационные активы',
                    'software': 'Программные средства',
                    'hardware': 'Аппаратные средства',
                    'other': 'Прочие активы'
                }
                
                type_groups = {'information': {}, 'software': {}, 'hardware': {}, 'other': {}}
                
                for asset_id, vul_dict in asset_vuln_map.items():
                    asset = asset_map.get(asset_id)
                    if not asset:
                        continue
                    
                    asset_type = asset.type if asset.type in type_groups else 'other'
                    type_groups[asset_type][asset_id] = vul_dict
                
                for asset_type, assets_dict in type_groups.items():
                    if not assets_dict:
                        continue
                    
                    elements.append(Paragraph(f"{type_names[asset_type]}", styles['Normal']))
                    elements.append(Spacer(1, 4))
                    
                    all_vul_ids = set()
                    for vul_dict in assets_dict.values():
                        all_vul_ids.update(vul_dict.keys())
                    
                    vul_ids_list = list(all_vul_ids)
                    
                    header_row = ['Актив']
                    for vid in vul_ids_list:
                        vul_obj = vul_map.get(vid)
                        if vul_obj and hasattr(vul_obj, 'name'):
                            header_row.append(vul_obj.name)
                        else:
                            header_row.append(str(vid))
                    
                    assessment_table_data = [header_row]
                    
                    for asset_id, vul_dict in assets_dict.items():
                        asset = asset_map.get(asset_id)
                        if not asset:
                            continue
                        
                        row = [asset.name]
                        for vul_id in vul_ids_list:
                            assessment = vul_dict.get(vul_id, '-')
                            row.append(assessment)
                        
                        assessment_table_data.append(row)
                    
                    assessment_table = create_standard_table(assessment_table_data, styles, num_columns=len(header_row))
                    elements.append(assessment_table)
                    elements.append(Spacer(1, 6))
            else:
                elements.append(Paragraph("Оценки уязвимостей не заполнены", styles['Normal']))
            
            elements.append(Spacer(1, 12))
            
        elif module == 'incidents':
            elements.append(PageBreak())
            elements.append(Paragraph("4. ИНЦИДЕНТЫ", styles['Title']))
            elements.append(Spacer(1, 8))
            
            query = db.session.query(Incident).join(Asset).join(Context)
            if context_id:
                query = query.filter(Asset.context_id == context_id)
            
            incidents = query.all()
            
            if incidents:
                elements.append(Paragraph("Подробная информация об инцидентах:", styles['Title']))
                elements.append(Spacer(1, 6))
                
                for incident in incidents:
                    elements.append(Paragraph(f"Инцидент #{incident.id}", styles['Normal']))
                    elements.append(Spacer(1, 4))
                    
                    operational_impact_text = ''
                    if incident.operational_impact:
                        try:
                            import json
                            impacts = json.loads(incident.operational_impact)
                            impact_names = []
                            if 'confidentiality' in impacts:
                                impact_names.append('Конфиденциальность')
                            if 'integrity' in impacts:
                                impact_names.append('Целостность')
                            if 'availability' in impacts:
                                impact_names.append('Доступность')
                            operational_impact_text = ', '.join(impact_names)
                        except:
                            operational_impact_text = incident.operational_impact or ''
                    
                    info_data = [
                        ['Параметр', 'Значение'],
                        ['ID', str(incident.id)],
                        ['Актив', incident.asset.name if incident.asset else ''],
                        ['Угроза', incident.threat.name if incident.threat else ''],
                        ['Уязвимость', incident.vulnerability.name if incident.vulnerability else ''],
                        ['Операционное воздействие', operational_impact_text],
                        ['Воздействие на бизнес', incident.business_impact or ''],
                        ['Уровень воздействия', incident.impact_level or ''],
                        ['Название сценария', incident.scenario_name or ''],
                        ['Вероятность сценария', str(incident.scenario_probability) if incident.scenario_probability else ''],
                        ['Дата создания', incident.created_at.strftime('%d.%m.%Y %H:%M:%S') if incident.created_at else '']
                    ]
                    
                    wrapped_info_data = create_table_data_with_wrapping(info_data, styles, max_length=50)
                    info_table = Table(wrapped_info_data, colWidths=[1.8*inch, 4.2*inch])
                    info_table.setStyle(create_detailed_table_style())
                    elements.append(info_table)
                    
                    
                    
                    if incident.treatment_plans:
                        elements.append(Spacer(1, 6))
                        elements.append(Paragraph("Планы обработки:", styles['Normal']))
                        plan_data = [['ID плана', 'Меры', 'Остаточный риск', 'Сроки', 'Ответственные']]
                        for plan in incident.treatment_plans:
                            plan_data.append([
                                str(plan.id),
                                (plan.risk_treatment_measures[:40] + "...") if plan.risk_treatment_measures and len(plan.risk_treatment_measures) > 40 else (plan.risk_treatment_measures or ''),
                                plan.residual_risk or '',
                                plan.deadlines or '',
                                plan.responsible_persons or ''
                            ])
                        
                        plan_table = Table(create_table_data_with_wrapping(plan_data, styles, max_length=35))
                        plan_table.setStyle(create_table_style())
                        elements.append(plan_table)
                    
                    elements.append(Spacer(1, 10))
            else:
                elements.append(Paragraph("Данные об инцидентах отсутствуют", styles['Normal']))
            
            elements.append(Spacer(1, 12))
            
        elif module == 'risks':
            elements.append(PageBreak())
            elements.append(Paragraph("5. РИСКИ", styles['Title']))
            elements.append(Spacer(1, 8))
            
            # Загружаем критерии принятия риска из контекста
            risk_acceptance_criteria = None
            if context_id:
                context = Context.query.get(context_id)
                if context and context.risk_acceptance_criteria:
                    try:
                        import json
                        risk_acceptance_criteria = json.loads(context.risk_acceptance_criteria)
                    except:
                        pass
            
            query = db.session.query(Risk).join(Incident).join(Asset).join(Context)
            if context_id:
                query = query.filter(Context.id == context_id)
            
            risks = query.all()
            
            if risks:
                elements.append(Paragraph("Подробная информация о рисках:", styles['Title']))
                elements.append(Spacer(1, 6))
                
                for risk in risks:
                    elements.append(Paragraph(f"Риск #{risk.id}", styles['Normal']))
                    elements.append(Spacer(1, 4))
                    
                    # Определяем приемлемость риска на основе критериев из контекста
                    is_acceptable = 'Нет'
                    risk_level = risk.risk_level or ''
                    
                    if risk_acceptance_criteria:
                        if risk_level == 'низкий':
                            is_acceptable = 'Да' if risk_acceptance_criteria.get('low') == 'приемлемый' else 'Нет'
                        elif risk_level == 'средний':
                            is_acceptable = 'Да' if risk_acceptance_criteria.get('medium') == 'приемлемый' else 'Нет'
                        elif risk_level == 'высокий':
                            is_acceptable = 'Да' if risk_acceptance_criteria.get('high') == 'приемлемый' else 'Нет'
                    else:
                        # По умолчанию: низкий и средний - приемлемый, высокий - неприемлемый
                        if risk.risk_score is not None:
                            is_acceptable = 'Да' if risk.risk_score < 5 else 'Нет'
                    
                    info_data = [
                        ['Параметр', 'Значение'],
                        ['ID', str(risk.id)],
                        ['Актив', risk.incident.asset.name if risk.incident and risk.incident.asset else ''],
                        ['Угроза', risk.incident.threat.name if risk.incident and risk.incident.threat else ''],
                        ['Уязвимость', risk.incident.vulnerability.name if risk.incident and risk.incident.vulnerability else ''],
                        ['Уровень последствий', risk.impact_level or ''],
                        ['Вероятность сценария', str(format_scenario_probability(risk.scenario_probability)) if risk.scenario_probability else ''],
                        ['Уровень риска', risk_level],
                        ['Приемлемый', is_acceptable],
                        ['Дата создания', risk.created_at.strftime('%d.%m.%Y %H:%M:%S') if risk.created_at else '']
                    ]
                    
                    wrapped_info_data = create_table_data_with_wrapping(info_data, styles, max_length=50)
                    info_table = Table(wrapped_info_data, colWidths=[1.8*inch, 4.2*inch])
                    info_table.setStyle(create_detailed_table_style())
                    elements.append(info_table)
                    elements.append(Spacer(1, 10))
            else:
                elements.append(Paragraph("Данные о рисках отсутствуют", styles['Normal']))
            
            elements.append(Spacer(1, 12))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

def get_assessment_level(value):
    """Получение уровня оценки по числовому значению"""
    if value is None:
        return 'Не оценено'
    if value >= 0.7 and value <= 1:
        return 'Высокая'
    if value >= 0.4 and value < 0.7:
        return 'Средняя'
    if value >= 0.25 and value < 0.4:
        return 'Минимальная'
    return 'Минимальная'

def format_scenario_probability(value):
    """Форматирование вероятности сценария"""
    if value is None:
        return ''
    try:
        num_value = float(value)
        if num_value <= 2:
            return f'низкая ({int(num_value)})'
        elif num_value <= 4:
            return f'средняя ({int(num_value)})'
        else:
            return f'высокая ({int(num_value)})'
    except (ValueError, TypeError):
        return str(value)
