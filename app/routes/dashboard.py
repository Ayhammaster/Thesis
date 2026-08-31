from flask import Blueprint, render_template, session, redirect, url_for

dashboard_bp = Blueprint('dashboard', __name__)

def require_login():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

@dashboard_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('dashboard.html', 
                         user_name=session.get('full_name'), 
                         user_role=session.get('role'))

@dashboard_bp.route('/<path:path>')
def catch_all(path):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('dashboard.html',
                         user_name=session.get('full_name'),
                         user_role=session.get('role'))
