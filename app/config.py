import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///iot.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'super-secret-key-for-session')

    # Email Settings
    EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS', "ayhamclash91@gmail.com")
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', "vunjqyjsusyzeetn")
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
