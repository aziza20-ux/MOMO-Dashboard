from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from sqlalchemy.exc import IntegrityError
from models.users import User, Base # Import User and Base from models
from database import get_db, engine # Import engine and get_db from database.py to create tables

auth_bp = Blueprint('auth', __name__)

# Ensure User table is created when auth_bp is loaded or when app initializes
# This is handled by init_db in database.py which is called from app.py
# Base.metadata.create_all(engine) # This line is moved to init_db() in database.py

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handles user registration.
    GET: Displays the registration form.
    POST: Processes the registration form submission, creates a new user.
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Username and password are required!', 'error')
            return render_template('register.html')

        with get_db() as db_session:
            try:
                new_user = User(username=username)
                new_user.set_password(password)
                db_session.add(new_user)
                db_session.commit()
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('auth.login'))
            except IntegrityError:
                db_session.rollback()
                flash('Username already exists. Please choose a different one.', 'error')
            except Exception as e:
                db_session.rollback()
                flash(f'An error occurred: {e}', 'error')
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handles user login.
    GET: Displays the login form.
    POST: Processes the login form submission, authenticates user.
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with get_db() as db_session:
            user = db_session.query(User).filter_by(username=username).first()

            if user and user.check_password(password):
                session['user_id'] = user.id
                session['username'] = user.username
                flash('Logged in successfully!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password.', 'error')
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """
    Logs out the current user by clearing the session.
    """
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

