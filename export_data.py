# export_data.py
import csv
from app import create_app
from app.extensions import db
from app.models import SensorReading

app = create_app()
with app.app_context():
    readings = SensorReading.query.order_by(SensorReading.timestamp.asc()).all()

    with open('sensor_data.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['sensor_type', 'value', 'timestamp'])
        for r in readings:
            writer.writerow([r.sensor_type, r.value, r.timestamp.strftime('%Y-%m-%d %H:%M:%S')])

    print(f"تم تصدير {len(readings)} قراءة إلى sensor_data.csv بنجاح!")