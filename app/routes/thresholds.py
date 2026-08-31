from flask import Blueprint, jsonify, request, session
from app.extensions import db
from app.models import Threshold, Setting
from app.utils.helpers import get_setting

thresholds_bp = Blueprint('thresholds', __name__)

def check_auth():
    if 'user_id' not in session:
        return jsonify({"error": "unauthorized"}), 401
    return None

@thresholds_bp.route('/thresholds', methods=['GET', 'POST'])
def manage_thresholds():
    auth = check_auth()
    if auth: return auth

    if request.method == 'POST':
        data = request.json
        t = Threshold.query.filter_by(sensor_type=data.get('sensor_type')).first()
        if not t:
            t = Threshold(sensor_type=data.get('sensor_type'))
            db.session.add(t)
        t.min_value = float(data.get('min_value'))
        t.max_value = float(data.get('max_value'))
        db.session.commit()
        return jsonify({"status": "success"}), 200

    thresholds = Threshold.query.all()
    return jsonify([{
        'sensor': t.sensor_type,
        'min': t.min_value,
        'max': t.max_value
    } for t in thresholds])

@thresholds_bp.route('/settings', methods=['GET', 'POST'])
def manage_settings():
    auth = check_auth()
    if auth: return auth

    if request.method == 'POST':
        email = request.json.get('alert_email')
        s = Setting.query.filter_by(key='alert_email').first()
        if not s:
            db.session.add(Setting(key='alert_email', value=email))
        else:
            s.value = email
        db.session.commit()
        return jsonify({"status": "success"}), 200

    return jsonify({'alert_email': get_setting('alert_email')})
