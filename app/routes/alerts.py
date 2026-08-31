from flask import Blueprint, jsonify, request, session
from app.extensions import db
from app.models import Alert

alerts_bp = Blueprint('alerts', __name__)

def check_auth():
    if 'user_id' not in session:
        return jsonify({"error": "unauthorized"}), 401
    return None

@alerts_bp.route('/alerts')
def get_alerts():
    auth = check_auth()
    if auth: return auth

    page = request.args.get('page', 1, type=int)
    pagination = (Alert.query
                 .order_by(Alert.timestamp.desc())
                 .paginate(page=page, per_page=20, error_out=False))

    alerts_data = [{
        'id': a.id,
        'msg': a.message,
        'time': a.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'email_sent': a.email_sent
    } for a in pagination.items]

    total = Alert.query.count()
    sent = Alert.query.filter_by(email_sent=True).count()

    return jsonify({
        'alerts': alerts_data,
        'page': page,
        'total_pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev,
        'stats': {
            'total': total,
            'sent': sent,
            'failed': total - sent
        }
    })

@alerts_bp.route('/alerts/<int:alert_id>', methods=['DELETE'])
def delete_alert(alert_id):
    auth = check_auth()
    if auth: return auth

    alert = Alert.query.get(alert_id)
    if alert:
        db.session.delete(alert)
        db.session.commit()
        return jsonify({"status": "deleted"}), 200
    return jsonify({"error": "not found"}), 404
