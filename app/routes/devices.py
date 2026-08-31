from flask import Blueprint, jsonify, request, session
from app.extensions import db
from app.models import Device, SensorReading, Alert, ControlCommand
from datetime import datetime

devices_bp = Blueprint('devices', __name__)

def check_auth():
    if 'user_id' not in session:
        return jsonify({"error": "unauthorized"}), 401
    return None

@devices_bp.route('/devices', methods=['GET', 'POST'])
def manage_devices():
    auth = check_auth()
    if auth: return auth

    if request.method == 'POST':
        code = request.json.get('device_code')
        name = request.json.get('name')
        encryption_key = request.json.get('encryption_key')
        protocol = request.json.get('protocol', 'HTTP')
        
        # التحقق من وجود الجهاز
        if Device.query.filter_by(device_code=code).first():
            return jsonify({"error": "Device exists"}), 400
        
        # إنشاء جهاز جديد
        dev = Device(
            device_code=code, 
            name=name, 
            status='offline',
            encryption_key=encryption_key,
            protocol=protocol,
            last_seen=datetime.utcnow()
        )
        db.session.add(dev)
        db.session.commit()
        return jsonify({"status": "success"}), 201

    # GET - جلب جميع الأجهزة
    devices = Device.query.all()
    return jsonify([{
        'id': d.id, 
        'code': d.device_code, 
        'name': d.name, 
        'status': d.status, 
        'uuid': d.device_uuid,
        'protocol': d.protocol, 
        'interval': d.interval_sec,
        'encryption_key': d.encryption_key,
        'last_seen': d.last_seen.strftime('%Y-%m-%d %H:%M:%S') if d.last_seen else None
    } for d in devices])

@devices_bp.route('/devices/<int:device_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_device(device_id):
    auth = check_auth()
    if auth: return auth
    
    dev = Device.query.get(device_id)
    if not dev:
        return jsonify({"error": "not found"}), 404
    
    # GET - عرض جهاز واحد
    if request.method == 'GET':
        return jsonify({
            'id': dev.id,
            'code': dev.device_code,
            'name': dev.name,
            'status': dev.status,
            'uuid': dev.device_uuid,
            'protocol': dev.protocol,
            'interval': dev.interval_sec,
            'encryption_key': dev.encryption_key,
            'last_seen': dev.last_seen.strftime('%Y-%m-%d %H:%M:%S') if dev.last_seen else None
        })
    
    # PUT - تحديث جهاز
    if request.method == 'PUT':
        data = request.json
        dev.name = data.get('name', dev.name)
        dev.protocol = data.get('protocol', dev.protocol)
        dev.encryption_key = data.get('encryption_key', dev.encryption_key)
        dev.interval_sec = data.get('interval', dev.interval_sec)
        
        db.session.commit()
        return jsonify({"status": "updated"}), 200
    
    # DELETE - حذف جهاز
    if request.method == 'DELETE':
        SensorReading.query.filter_by(device_id=device_id).delete()
        Alert.query.filter_by(device_id=device_id).delete()
        ControlCommand.query.filter_by(device_id=device_id).delete()
        db.session.delete(dev)
        db.session.commit()
        return jsonify({"status": "deleted"}), 200

@devices_bp.route('/devices/<int:device_id>/status', methods=['PUT'])
def update_device_status(device_id):
    """تحديث حالة جهاز معين"""
    auth = check_auth()
    if auth: return auth
    
    dev = Device.query.get(device_id)
    if not dev:
        return jsonify({"error": "not found"}), 404
    
    status = request.json.get('status')
    if status in ['online', 'offline']:
        dev.status = status
        if status == 'online':
            dev.last_seen = datetime.utcnow()
        db.session.commit()
        return jsonify({"status": "updated"}), 200
    
    return jsonify({"error": "Invalid status"}), 400