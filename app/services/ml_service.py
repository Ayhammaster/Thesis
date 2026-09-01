import os
import numpy as np
import joblib
from app.models import SensorReading

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'models')
SEQ_LENGTH = 10  # نفس طول التسلسل المستخدم في التدريب

_models_cache = {}

def _load_models(sensor_type):
    """تحميل نموذج المستشعر مع كاش (LSTM + Scaler + Isolation Forest)."""
    if sensor_type in _models_cache:
        return _models_cache[sensor_type]

    paths = {
        'lstm': os.path.join(MODELS_DIR, f'{sensor_type}_lstm.keras'),
        'scaler': os.path.join(MODELS_DIR, f'{sensor_type}_scaler.pkl'),
        'iforest': os.path.join(MODELS_DIR, f'{sensor_type}_iforest.pkl'),
    }
    if not all(os.path.exists(p) for p in paths.values()):
        _models_cache[sensor_type] = None
        return None

    from tensorflow.keras.models import load_model
    _models_cache[sensor_type] = {
        'lstm': load_model(paths['lstm'], compile=False),
        'scaler': joblib.load(paths['scaler']),
        'iforest': joblib.load(paths['iforest'])
    }
    return _models_cache[sensor_type]

def predict_hybrid(sensor_type):
    """
    تقييم آخر قراءة بالنموذج الهجين المدرب (LSTM + Isolation Forest).
    يعيد dict فيه نتيجة LSTM ونتيجة Isolation Forest، أو None إذا لم تتوفر البيانات/النماذج.
    """
    bundle = _load_models(sensor_type)
    if not bundle:
        return None

    readings = (SensorReading.query
                .filter_by(sensor_type=sensor_type)
                .order_by(SensorReading.timestamp.desc())
                .limit(SEQ_LENGTH + 1)
                .all())[::-1]  # ترتيب زمني تصاعدي مثل التدريب

    if len(readings) < SEQ_LENGTH + 1:
        return None

    values = np.array([r.value for r in readings], dtype=np.float64).reshape(-1, 1)
    scaled = bundle['scaler'].transform(values)

    seq = scaled[:SEQ_LENGTH].reshape(1, SEQ_LENGTH, 1)
    actual = float(scaled[SEQ_LENGTH, 0])
    last_timestamp = readings[-1].timestamp
    hour = last_timestamp.hour  # ميزة ساعة اليوم المستخدمة في التدريب

    pred = float(bundle['lstm'].predict(seq, verbose=0)[0][0])
    residual = abs(pred - actual)

    features = np.array([[actual, residual, hour]])
    if_pred = bundle['iforest'].predict(features)[0]          # 1 طبيعي / -1 شاذ
    if_score = bundle['iforest'].decision_function(features)[0]  # كلما قلّ كان أشد شذوذاً

    # تحويل درجة IF إلى نسبة شذوذ 0-100: قراءة طبيعية أقل من 50% وشاذة أعلى منها
    if if_pred == 1:
        anomaly_pct = max(0.0, min(49.0, 50.0 - float(if_score) * 200.0))
    else:
        anomaly_pct = max(51.0, min(100.0, 50.0 - float(if_score) * 200.0))

    return {
        'lstm_pred_scaled': round(pred, 4),
        'actual_scaled': round(actual, 4),
        'residual': round(residual, 4),
        'hour': hour,
        'if_prediction': int(if_pred),
        'if_score': round(float(if_score), 4),
        'anomaly_pct': round(anomaly_pct, 1),
        'is_anomaly': bool(if_pred == -1)
    }
