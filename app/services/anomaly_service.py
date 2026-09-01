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

    @staticmethod
    def detect_all(value, sensor_type, device_id=None, latency_ms=0, threshold_z=3.0, history_limit=30):
        query = SensorReading.query.filter_by(sensor_type=sensor_type)
        if device_id:
            query = query.filter_by(device_id=device_id)
        history = (query
                   .order_by(SensorReading.timestamp.desc())
                   .limit(history_limit)
                   .all())

        values = [r.value for r in history]
        stat_score = 0.0
        stat_anomaly = False
        if len(values) >= 5:
            mean = sum(values) / len(values)
            variance = sum([(x - mean) ** 2 for x in values]) / len(values)
            std_dev = math.sqrt(variance)
            if std_dev > 0:
                stat_score = round(abs((value - mean) / std_dev), 2)
                if stat_score > threshold_z:
                    stat_anomaly = True

        # نموذج ML مبسط للقيمة: يعتمد على مدى القيم التاريخية (IQR)
        ml_sensor_score = 0.5
        ml_sensor_anomaly = False
        if len(values) >= 5:
            sorted_v = sorted(values)
            q1 = sorted_v[len(sorted_v) // 4]
            q3 = sorted_v[(len(sorted_v) * 3) // 4]
            iqr = q3 - q1
            if iqr > 0 and (value < q1 - 1.5 * iqr or value > q3 + 1.5 * iqr):
                ml_sensor_anomaly = True
                ml_sensor_score = -0.8

        # نموذج ML مبسط للتأخير: يعتمد على متوسط التأخير التاريخي
        ml_latency_score = 0.5
        ml_latency_anomaly = False
        latencies = [r.latency_ms for r in history if r.latency_ms and r.latency_ms > 0]
        if len(latencies) >= 5:
            lat_mean = sum(latencies) / len(latencies)
            if lat_mean > 0 and latency_ms > lat_mean * 3:
                ml_latency_anomaly = True
                ml_latency_score = -0.8

        is_anomaly = stat_anomaly or ml_sensor_anomaly or ml_latency_anomaly
        return {
            'is_anomaly': is_anomaly,
            'anomaly_score': ml_sensor_score if ml_sensor_anomaly else stat_score,
            'models': {
                'statistical': {'name': 'إحصائي (Z-Score)', 'score': stat_score, 'is_anomaly': stat_anomaly},
                'ml_sensor': {'name': 'ذكاء المستشعر (IQR)', 'score': ml_sensor_score, 'is_anomaly': ml_sensor_anomaly},
                'ml_latency': {'name': 'ذكاء زمن الاستجابة', 'score': ml_latency_score, 'is_anomaly': ml_latency_anomaly}
            }
        }
