from flask import Flask
from app.config import Config
from app.extensions import db
from app.services.email_service import EmailService

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)

    # Initialize services
    app.email_service = EmailService()

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.devices import devices_bp
    from app.routes.sensors import sensors_bp
    from app.routes.thresholds import thresholds_bp
    from app.routes.alerts import alerts_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(devices_bp, url_prefix='/api')
    app.register_blueprint(sensors_bp, url_prefix='/api')
    app.register_blueprint(thresholds_bp, url_prefix='/api')
    app.register_blueprint(alerts_bp, url_prefix='/api')

    # Create tables and seed data
    with app.app_context():
        db.create_all()
        from app.utils.seeders import seed_database
        seed_database()

    return app
