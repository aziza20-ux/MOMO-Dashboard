from functools import wraps
from flask import session, flash, redirect, url_for

def login_required(f):
    """
    Decorator to protect routes, ensuring only authenticated users can access them.
    If the user is not logged in, they are redirected to the login page.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function
