import math
from app.models import SensorReading

class AnomalyDetector:
    @staticmethod
    def detect(value, sensor_type, threshold_z=3.0, history_limit=30):
        history = (SensorReading.query
                  .filter_by(sensor_type=sensor_type)
                  .order_by(SensorReading.timestamp.desc())
                  .limit(history_limit)
                  .all())

        values = [r.value for r in history]
        is_anomaly = False
        anomaly_score = 0.0

        if len(values) >= 5:
            mean = sum(values) / len(values)
            variance = sum([(x - mean) ** 2 for x in values]) / len(values)
            std_dev = math.sqrt(variance)
            if std_dev > 0:
                z_score = abs((value - mean) / std_dev)
                anomaly_score = round(z_score, 2)
                if z_score > threshold_z:
                    is_anomaly = True

        return {
            'is_anomaly': is_anomaly,
            'anomaly_score': anomaly_score,
            'z_score': anomaly_score,
            'sample_size': len(values)
        }
