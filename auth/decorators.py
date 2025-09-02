# auth/decorators.py
from functools import wraps
from flask import session, redirect, url_for, flash

def role_required(*allowed_roles):
    """
    A decorator to protect routes, ensuring the logged-in user has one of the allowed roles.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if a user is logged in
            if 'user_role' not in session:
                flash('You must be logged in to view this page.', 'error')
                return redirect(url_for('view_bp.login'))

            # If the user's role is not in the allowed list, redirect to the 'unauthorized' page.
            if session['user_role'] not in allowed_roles:
                return redirect(url_for('view_bp.unauthorized'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator