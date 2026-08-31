import paho.mqtt.client as mqtt
import json
from datetime import datetime, timedelta
from app.extensions import db
from app.models import Device, SensorReading, Alert, Threshold
from app.services.anomaly_service import AnomalyDetector
from flask import current_app

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "iot/anomaly/data"

def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT Broker with result code {rc}")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    # هذه الدالة تعمل في خيط منفصل (Background Thread)
    # لذلك يجب استخدام App Context للوصول لقاعدة البيانات
    app = userdata['app']
    with app.app_context():
        try:
            data = json.loads(msg.payload.decode())
            
            # نفس منطق الـ HTTP بالضبط!
            device_code = data.get('device_id')
            device = Device.query.filter_by(device_code=device_code).first()
            server_time = datetime.utcnow() + timedelta(hours=3)

            if not device:
                device = Device(
                    device_code=device_code, name=f'جهاز {device_code}',
                    status='online', last_seen=server_time, protocol='MQTT',
                    encryption_key=data.get('encryption_key')
                )
                db.session.add(device)
            else:
                if device.encryption_key and device.encryption_key != data.get('encryption_key'):
                    return # مفتاح خاطئ
                
                device.status = 'online'
                device.last_seen = server_time
                device.protocol = 'MQTT'

            sensor_type = data.get('sensor_type')
            value = float(data.get('value'))

            # حساب التأخير
            client_time_str = data.get('client_time')
            latency_ms = 0
            if client_time_str:
                client_time = datetime.fromtimestamp(int(client_time_str) / 1000.0)
                latency_ms = int((server_time - client_time).total_seconds() * 1000)
                if latency_ms < 0: latency_ms = 0

            # كشف الشذوذ
            anomaly_result = AnomalyDetector.detect_all(value, sensor_type, device.id, latency_ms)

            reading = SensorReading(
                device_id=device.id, sensor_type=sensor_type, value=value,
                timestamp=server_time, latency_ms=latency_ms,
                is_anomaly=anomaly_result['is_anomaly'],
                anomaly_score=anomaly_result['models']['ml_sensor']['score']
            )
            db.session.add(reading)
            db.session.commit()
            
            print(f"✅ MQTT Data Received & Saved: {sensor_type}={value}, Latency={latency_ms}ms")

        except Exception as e:
            print(f"MQTT Error: {e}")

def start_mqtt_listener(app):
    client = mqtt.Client(userdata={'app': app})
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever() # استماع دائم
    except Exception as e:
        print(f"Failed to connect to MQTT Broker: {e}")