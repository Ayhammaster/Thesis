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
        from app.services.ml_service import predict_hybrid

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

        # النموذج الهجين المدرب: LSTM + Isolation Forest
        hybrid = predict_hybrid(sensor_type)
        if hybrid:
            lstm_anomaly = hybrid['residual'] > 0.15  # خطأ تنبؤ كبير = سلوك غير اعتيادي
            iforest_anomaly = hybrid['is_anomaly']
            lstm_score = round(hybrid['residual'] * 100, 1)      # نسبة خطأ التنبؤ %
            iforest_score = hybrid['anomaly_pct']                # نسبة الشذوذ %
        else:
            lstm_anomaly = iforest_anomaly = False
            lstm_score = iforest_score = 0.0

        is_anomaly = stat_anomaly or lstm_anomaly or iforest_anomaly
        return {
            'is_anomaly': is_anomaly,
            'anomaly_score': stat_score,
            'hybrid': hybrid,
            'models': {
                'statistical': {'name': 'إحصائي (Z-Score)', 'score': stat_score, 'is_anomaly': stat_anomaly},
                'ml_sensor': {'name': 'شبكة LSTM المدربة', 'score': lstm_score, 'is_anomaly': lstm_anomaly},
                'ml_latency': {'name': 'غابة العزل Isolation Forest', 'score': iforest_score, 'is_anomaly': iforest_anomaly}
            }
        }
