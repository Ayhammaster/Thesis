from flask import Blueprint, jsonify, request, session, current_app
from datetime import datetime, timedelta
from sqlalchemy import func
from app.extensions import db
from app.models import Device, SensorReading, Alert, Threshold
from app.services.anomaly_service import AnomalyDetector
from app.utils.helpers import get_setting

sensors_bp = Blueprint('sensors', __name__)

def check_auth():
    if 'user_id' not in session:
        return jsonify({"error": "unauthorized"}), 401
    return None

@sensors_bp.route('/data', methods=['POST'])
def receive_data():
    data = request.json
    device_code = data.get('device_id')
    device = Device.query.filter_by(device_code=device_code).first()

    server_time = datetime.utcnow() + timedelta(hours=3)

    if not device:
        device = Device(
            device_code=device_code,
            name=f'جهاز {device_code}',
            status='online',
            last_seen=server_time,
            device_uuid=data.get('uuid', 'N/A'),
            protocol=data.get('protocol', 'HTTP'),
            interval_sec=data.get('interval', 10)
        )
        db.session.add(device)
    else:
        device.status = 'online'
        device.last_seen = server_time
        if data.get('uuid'): device.device_uuid = data.get('uuid')
        if data.get('protocol'): device.protocol = data.get('protocol')
        if data.get('interval'): device.interval_sec = data.get('interval')

    sensor_type = data.get('sensor_type')
    value = float(data.get('value'))

    # Calculate latency
    client_time_str = data.get('client_time')
    latency_ms = 0
    if client_time_str:
        try:
            client_time = datetime.fromtimestamp(int(client_time_str) / 1000.0)
            latency_ms = int((server_time - client_time).total_seconds() * 1000)
            if latency_ms < 0: latency_ms = 0
        except: pass

    # Anomaly detection
    anomaly_result = AnomalyDetector.detect(value, sensor_type)

    reading = SensorReading(
        device_id=device.id,
        sensor_type=sensor_type,
        value=value,
        timestamp=server_time,
        latency_ms=latency_ms,
        is_anomaly=anomaly_result['is_anomaly'],
        anomaly_score=anomaly_result['anomaly_score']
    )
    db.session.add(reading)

    # Check thresholds and send alerts
    threshold = Threshold.query.filter_by(sensor_type=sensor_type).first()
    target_email = get_setting('alert_email')

    if threshold and (value < threshold.min_value or value > threshold.max_value):
        alert_msg = (f"تنبيه!\nالجهاز: {device.name}\n"
                    f"المستشعر: {sensor_type}\nالقيمة: {value}\n"
                    f"تجاوز الحدود ({threshold.min_value} - {threshold.max_value}).")
        email_status = current_app.email_service.send_alert(
            f"تنبيه من {device.name}", alert_msg, target_email
        )
        db.session.add(Alert(device_id=device.id, message=alert_msg, email_sent=email_status))

    if anomaly_result['is_anomaly']:
        security_msg = (f"⚠️ تنبيه أمني!\nالجهاز: {device.name}\n"
                       f"سلوك غير اعتيادي مكتشف (الدرجة: {anomaly_result['anomaly_score']}).")
        email_status = current_app.email_service.send_alert(
            "تنبيه أمني - حالة غير اعتيادية", security_msg, target_email
        )
        db.session.add(Alert(device_id=device.id, message=security_msg, email_sent=email_status))

    # Update offline devices
    time_threshold = server_time - timedelta(minutes=5)
    offline_devices = Device.query.filter(Device.last_seen < time_threshold).all()
    for dev in offline_devices:
        dev.status = 'offline'

    db.session.commit()
    return jsonify({
        "status": "success",
        "latency_ms": latency_ms,
        "is_anomaly": anomaly_result['is_anomaly']
    }), 200

@sensors_bp.route('/current-readings')
def current_readings():
    auth = check_auth()
    if auth: return auth

    # Update offline devices
    server_time = datetime.utcnow() + timedelta(hours=3)
    time_threshold = server_time - timedelta(minutes=5)
    offline_devices = Device.query.filter(Device.last_seen < time_threshold).all()
    for dev in offline_devices:
        dev.status = 'offline'
    db.session.commit()

    device_id = request.args.get('device_id', type=int)
    result = {}

    for sensor_type in ['temperature', 'humidity']:
        query = SensorReading.query.filter_by(sensor_type=sensor_type)
        if device_id:
            query = query.filter_by(device_id=device_id)
        last = query.order_by(SensorReading.timestamp.desc()).first()

        if last:
            result[sensor_type] = {
                'value': last.value,
                'timestamp': last.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }
        else:
            result[sensor_type] = None
    return jsonify(result)

@sensors_bp.route('/sensor-stats/<sensor_type>')
def sensor_stats(sensor_type):
    auth = check_auth()
    if auth: return auth

    device_id = request.args.get('device_id', type=int)
    query = SensorReading.query.filter_by(sensor_type=sensor_type)
    if device_id:
        query = query.filter_by(device_id=device_id)
    readings = query.all()

    if not readings:
        return jsonify({'min': 0, 'max': 0, 'avg': 0, 'count': 0})

    values = [r.value for r in readings]
    return jsonify({
        'min': min(values),
        'max': max(values),
        'avg': round(sum(values)/len(values), 2),
        'count': len(values)
    })

@sensors_bp.route('/charts')
def get_charts():
    auth = check_auth()
    if auth: return auth

    filter_date = request.args.get('date')
    device_id = request.args.get('device_id', type=int)

    # Build base queries
    temp_query = SensorReading.query.filter_by(sensor_type='temperature')
    hum_query = SensorReading.query.filter_by(sensor_type='humidity')

    # Apply device filter if provided
    if device_id:
        temp_query = temp_query.filter_by(device_id=device_id)
        hum_query = hum_query.filter_by(device_id=device_id)

    # Apply date filter if provided
    if filter_date and filter_date.strip():
        temp_readings = temp_query.filter(
            func.date(SensorReading.timestamp) == filter_date
        ).order_by(SensorReading.timestamp.asc()).all()
        hum_readings = hum_query.filter(
            func.date(SensorReading.timestamp) == filter_date
        ).order_by(SensorReading.timestamp.asc()).all()
    else:
        # Get last 30 readings if no date filter
        temp_readings = temp_query.order_by(SensorReading.timestamp.desc()).limit(30).all()[::-1]
        hum_readings = hum_query.order_by(SensorReading.timestamp.desc()).limit(30).all()[::-1]

    return jsonify({
        'temperature': {
            'labels': [r.timestamp.strftime('%H:%M') for r in temp_readings],
            'data': [r.value for r in temp_readings]
        },
        'humidity': {
            'labels': [r.timestamp.strftime('%H:%M') for r in hum_readings],
            'data': [r.value for r in hum_readings]
        }
    })


@sensors_bp.route('/available-days/<sensor_type>')
def get_available_days(sensor_type):
    auth = check_auth()
    if auth: return auth

    try:
        days = (db.session.query(func.date(SensorReading.timestamp).label('date_str'))
               .filter_by(sensor_type=sensor_type)
               .distinct()
               .order_by(func.date(SensorReading.timestamp).desc())
               .all())

        # تحويل التواريخ إلى نصوص لتجنب أخطاء JSON
        result = [str(d.date_str) for d in days]
        return jsonify(result)
    except Exception as e:
        print(f"Error fetching days: {e}")
        return jsonify([]), 200

@sensors_bp.route('/models-comparison')
def models_comparison():
    auth = check_auth()
    if auth: return auth

    last = (SensorReading.query
            .order_by(SensorReading.timestamp.desc())
            .first())
    if not last:
        return jsonify({'message': 'لا توجد قراءات بعد لتحليل النماذج.'})

    result = AnomalyDetector.detect_all(last.value, last.sensor_type, last.device_id, last.latency_ms or 0)
    result['value'] = last.value
    result['latency_ms'] = last.latency_ms or 0
    result['sensor_type'] = last.sensor_type
    return jsonify(result)

@sensors_bp.route('/latency-comparison')
def latency_comparison():
    auth = check_auth()
    if auth: return auth

    result = {}
    for protocol in ['HTTP', 'MQTT']:
        rows = (db.session.query(SensorReading.latency_ms)
                .join(Device, SensorReading.device_id == Device.id)
                .filter(Device.protocol == protocol,
                        SensorReading.latency_ms.isnot(None),
                        SensorReading.latency_ms > 0)
                .all())
        values = [r[0] for r in rows]
        if values:
            result[protocol] = {
                'avg': round(sum(values) / len(values), 1),
                'min': min(values),
                'max': max(values),
                'count': len(values)
            }
        else:
            result[protocol] = {'avg': 0, 'min': 0, 'max': 0, 'count': 0}

    diff = round(result['HTTP']['avg'] - result['MQTT']['avg'], 1)
    result['difference'] = {
        'avg': diff,
        'faster_protocol': 'MQTT' if diff > 0 else ('HTTP' if diff < 0 else 'متساوي')
    }
    return jsonify(result)

@sensors_bp.route('/sensor-data', methods=['DELETE'])
def clear_sensor_data():
    auth = check_auth()
    if auth: return auth

    sensor_type = request.args.get('sensor_type')
    if sensor_type:
        SensorReading.query.filter_by(sensor_type=sensor_type).delete()
    else:
        SensorReading.query.delete()
    db.session.commit()
    return jsonify({"status": "cleared"}), 200