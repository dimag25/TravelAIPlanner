from flask import Blueprint, flash, redirect, render_template, request, url_for, session
from flask_login import current_user, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from app import db, app
from models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if email already exists (case-insensitive)
        existing_user = User.query.filter(func.lower(User.email) == func.lower(email)).first()
        if existing_user:
            flash('This email is already registered. Please use another email or login to your existing account.', 'danger')
            return redirect(url_for('auth.register'))
            
        try:
            user = User(username=username, email=email)
            user.password_hash = generate_password_hash(password)
            
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! Welcome to AI Travel Planner.', 'success')
            login_user(user)
            return redirect(url_for('dashboard'))
            
        except IntegrityError as e:
            db.session.rollback()
            if 'username' in str(e.orig):
                flash('This username is already taken. Please choose another one.', 'danger')
            else:
                flash('An error occurred during registration. Please try again.', 'danger')
            return redirect(url_for('auth.register'))
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        remember = request.form.get('remember', False)
        
        app.logger.debug(f"Login attempt for email: {email}")
        
        # Case-insensitive email query
        user = User.query.filter(func.lower(User.email) == func.lower(email)).first()
        app.logger.debug(f"User found: {user is not None}")
        
        if user and check_password_hash(user.password_hash, password):
            app.logger.debug("Password verified successfully")
            login_user(user, remember=remember)
            session.permanent = remember
            
            # Get the next page from the session or default to dashboard
            next_page = session.get('next', url_for('dashboard'))
            session.pop('next', None)
            
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page)
        
        app.logger.debug("Password verification failed")
        flash('Invalid email or password. Please check your credentials and try again.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Store the next page in session if provided
    if request.args.get('next'):
        session['next'] = request.args.get('next')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    if current_user.is_authenticated:
        username = current_user.username
        logout_user()
        flash(f'Goodbye {username}! You have been logged out successfully.', 'success')
    return redirect(url_for('index'))
