from functools import wraps

from flask import current_app, redirect, render_template, request, session, url_for


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('dashboard.login', next=request.url))
        return f(*args, **kwargs)
    return decorated


def login_view():
    error = None
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == current_app.config['DASHBOARD_PASSWORD']:
            session['authenticated'] = True
            next_url = request.args.get('next', url_for('dashboard.index'))
            return redirect(next_url)
        error = 'Password incorrect'
    return render_template('login.html', error=error)


def logout_view():
    session.clear()
    return redirect(url_for('dashboard.login'))
