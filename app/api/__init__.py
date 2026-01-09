from flask import Blueprint

# Создание蓝图 для каждого модуля
context_bp = Blueprint('contexts', __name__, url_prefix='/api/contexts')
asset_bp = Blueprint('assets', __name__, url_prefix='/api/assets')
asset_value_bp = Blueprint('asset_values', __name__, url_prefix='/api/asset-values')
asset_dependency_bp = Blueprint('asset_dependencies', __name__, url_prefix='/api/asset-dependencies')
damage_scale_bp = Blueprint('damage_scales', __name__, url_prefix='/api/damage-scales')
asset_security_property_impact_bp = Blueprint('asset_security_property_impacts', __name__, url_prefix='/api/asset-security-property-impacts')
asset_value_result_bp = Blueprint('asset_value_results', __name__, url_prefix='/api/asset-value-results')
threat_bp = Blueprint('threats', __name__, url_prefix='/api/threats')
vulnerability_bp = Blueprint('vulnerabilities', __name__, url_prefix='/api/vulnerabilities')
incident_bp = Blueprint('incidents', __name__, url_prefix='/api/incidents')
risk_bp = Blueprint('risks', __name__, url_prefix='/api/risks')
treatment_bp = Blueprint('treatments', __name__, url_prefix='/api/treatment_plans')