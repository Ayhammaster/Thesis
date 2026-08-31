from app.models import Setting

def get_setting(key, default=''):
    setting = Setting.query.filter_by(key=key).first()
    return setting.value if setting else default

def format_datetime(dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S') if dt else '--'

def format_date(dt):
    return dt.strftime('%Y-%m-%d') if dt else '--'
