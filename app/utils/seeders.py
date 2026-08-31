from werkzeug.security import generate_password_hash
from app.extensions import db
from app.models import User, Threshold

def seed_database():
    if not User.query.filter_by(username='doctor').first():
        db.session.add(User(
            username='doctor',
            password_hash=generate_password_hash('doctor123'),
            full_name='أ.د. محمد حجوز',
            role='admin'
        ))

    if not User.query.filter_by(username='student').first():
        db.session.add(User(
            username='student',
            password_hash=generate_password_hash('student123'),
            full_name='أيهم أحمد',
            role='operator'
        ))

    if not Threshold.query.filter_by(sensor_type='temperature').first():
        db.session.add(Threshold(sensor_type='temperature', min_value=15, max_value=35))

    if not Threshold.query.filter_by(sensor_type='humidity').first():
        db.session.add(Threshold(sensor_type='humidity', min_value=30, max_value=80))

    db.session.commit()
