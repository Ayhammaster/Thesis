from app.extensions import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(128))
    role = db.Column(db.String(20), default='viewer')

class Device(db.Model):
    __tablename__ = 'devices'
    id = db.Column(db.Integer, primary_key=True)
    device_code = db.Column(db.String(32), unique=True, nullable=False)
    name = db.Column(db.String(128))
    status = db.Column(db.String(20), default='offline')
    device_uuid = db.Column(db.String(64))
    protocol = db.Column(db.String(10), default='HTTP')
    interval_sec = db.Column(db.Integer, default=10)
    encryption_key = db.Column(db.String(128))
    last_seen = db.Column(db.DateTime)

    readings = db.relationship('SensorReading', backref='device', lazy=True, cascade='all, delete-orphan')
    alerts = db.relationship('Alert', backref='device', lazy=True, cascade='all, delete-orphan')
    commands = db.relationship('ControlCommand', backref='device', lazy=True, cascade='all, delete-orphan')

class SensorReading(db.Model):
    __tablename__ = 'sensor_readings'
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    sensor_type = db.Column(db.String(32), nullable=False)
    value = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now())
    latency_ms = db.Column(db.Integer)
    protocol = db.Column(db.String(10))  # البروتوكول المستخدم لحظة استلام القراءة
    is_anomaly = db.Column(db.Boolean, default=False)
    anomaly_score = db.Column(db.Float)

class Threshold(db.Model):
    __tablename__ = 'thresholds'
    id = db.Column(db.Integer, primary_key=True)
    sensor_type = db.Column(db.String(32), nullable=False, unique=True)
    min_value = db.Column(db.Float, nullable=False)
    max_value = db.Column(db.Float, nullable=False)

class Alert(db.Model):
    __tablename__ = 'alerts'
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now())
    is_read = db.Column(db.Boolean, default=False)
    email_sent = db.Column(db.Boolean, default=False)

class ControlCommand(db.Model):
    __tablename__ = 'control_commands'
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    command = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(20), default='sent')

class Setting(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    value = db.Column(db.String(256), nullable=False)
