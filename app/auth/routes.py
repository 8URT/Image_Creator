from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app.auth import bp
from app.models import User, UsageLog
from app import db
from app.config import Config
from datetime import datetime
import hashlib
import secrets

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page with username/password and Google OAuth"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))
        
        if not email or not password:
            flash('Please provide both email and password.', 'error')
            return render_template('login.html')
        
        # Try to find user by email or username
        user = User.query.filter(
            (User.email == email) | (User.username == email)
        ).first()
        
        if user and user.password_hash and check_password_hash(user.password_hash, password):
            if not user.is_active:
                flash('Your account has been disabled. Please contact an administrator.', 'error')
                return render_template('login.html')
            
            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            login_user(user, remember=remember)
            flash(f'Welcome back, {user.username or user.email}!', 'success')
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('main.index'))
        else:
            flash('Invalid email/username or password.', 'error')
    
    # Google OAuth URL
    google_auth_url = None
    if Config.GOOGLE_CLIENT_ID:
        google_auth_url = url_for('auth.google_login', _external=True)
    
    return render_template('login.html', google_auth_url=google_auth_url)

@bp.route('/google/login')
def google_login():
    """Initiate Google OAuth login"""
    if not Config.GOOGLE_CLIENT_ID:
        flash('Google OAuth is not configured.', 'error')
        return redirect(url_for('auth.login'))
    
    try:
        from app import oauth
        # Generate a nonce for security
        nonce = secrets.token_urlsafe(32)
        session['oauth_nonce'] = nonce
        
        redirect_uri = url_for('auth.google_callback', _external=True)
        # Use authorize_redirect with nonce parameter
        return oauth.google.authorize_redirect(redirect_uri, nonce=nonce)
    except Exception as e:
        import logging
        import traceback
        error_msg = str(e)
        logging.error(f'Google OAuth login error: {error_msg}', exc_info=True)
        logging.error(f'Traceback: {traceback.format_exc()}')
        # Show detailed error in development
        if hasattr(Config, 'FLASK_ENV') and Config.FLASK_ENV == 'development':
            flash(f'Failed to initiate Google login: {error_msg}', 'error')
        else:
            flash('Failed to initiate Google login.', 'error')
        return redirect(url_for('auth.login'))

@bp.route('/google/callback')
def google_callback():
    """Handle Google OAuth callback"""
    if not Config.GOOGLE_CLIENT_ID:
        flash('Google OAuth is not configured.', 'error')
        return redirect(url_for('auth.login'))
    
    try:
        from app import oauth
        token = oauth.google.authorize_access_token()
        
        # Get nonce from session
        nonce = session.pop('oauth_nonce', None)
        if not nonce:
            flash('OAuth session expired. Please try again.', 'error')
            return redirect(url_for('auth.login'))
        
        user_info = oauth.google.parse_id_token(token, nonce=nonce)
        
        google_id = user_info.get('sub')
        email = user_info.get('email')
        name = user_info.get('name', '')
        
        if not google_id or not email:
            flash('Failed to retrieve user information from Google.', 'error')
            return redirect(url_for('auth.login'))
        
        # Access control: Only allow login if GOOGLE_ALLOWED_DOMAINS is not set,
        # or if the user's email domain is in the allowed list.
        if Config.GOOGLE_ALLOWED_DOMAINS:
            allowed_domains = [d.strip() for d in Config.GOOGLE_ALLOWED_DOMAINS.split(',')]
            user_domain = email.split('@')[-1]
            if user_domain not in allowed_domains:
                flash(f'Access denied. Your email domain ({user_domain}) is not authorized.', 'error')
                return redirect(url_for('auth.login'))
        
        # Find or create user
        user = User.query.filter_by(google_id=google_id).first()
        
        if not user:
            # Check if user exists with this email
            user = User.query.filter_by(email=email).first()
            if user:
                # Link Google account to existing user
                user.google_id = google_id
                if not user.username and name:
                    user.username = name.split()[0].lower() if name else None
            else:
                # Check if new users are allowed via Google OAuth
                if not Config.GOOGLE_OAUTH_ALLOW_NEW_USERS:
                    flash('Google OAuth login is restricted to existing users only. Please contact an administrator to create an account.', 'error')
                    return redirect(url_for('auth.login'))
                
                # Create new user (only if allowed)
                # Generate username from name or email
                if name:
                    username = name.split()[0].lower() if name.split() else None
                else:
                    username = email.split('@')[0] if email else None
                
                # Ensure username is unique
                base_username = username
                counter = 1
                while username and User.query.filter_by(username=username).first():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                user = User(
                    email=email,
                    username=username,
                    google_id=google_id,
                    is_admin=False,
                    is_active=True
                )
                db.session.add(user)
        
        if not user.is_active:
            flash('Your account has been disabled. Please contact an administrator.', 'error')
            return redirect(url_for('auth.login'))
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        login_user(user)
        flash(f'Welcome, {user.username or user.email}!', 'success')
        
        next_page = request.args.get('next') or session.get('next')
        if next_page:
            session.pop('next', None)
            return redirect(next_page)
        return redirect(url_for('main.index'))
        
    except Exception as e:
        import logging
        import traceback
        error_msg = str(e)
        logging.error(f'Google OAuth error: {error_msg}', exc_info=True)
        logging.error(f'Traceback: {traceback.format_exc()}')
        # Show more detailed error in development
        if hasattr(Config, 'FLASK_ENV') and Config.FLASK_ENV == 'development':
            flash(f'Authentication failed: {error_msg}', 'error')
        else:
            flash('Authentication failed. Please try again.', 'error')
        return redirect(url_for('auth.login'))

@bp.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@bp.route('/fallback', methods=['GET', 'POST'])
def fallback_login():
    """Fallback password protection (emergency access)"""
    if not Config.FALLBACK_PASSWORD_ENABLED:
        flash('Fallback authentication is disabled.', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        
        if password:
            # Hash password and compare
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            if password_hash == Config.FALLBACK_PASSWORD_HASH:
                # Create or get fallback user
                user = User.query.filter_by(email='fallback@emergency.local').first()
                if not user:
                    user = User(
                        email='fallback@emergency.local',
                        username='emergency',
                        is_admin=False,
                        is_active=True
                    )
                    db.session.add(user)
                    db.session.commit()
                
                login_user(user)
                flash('Emergency access granted.', 'warning')
                return redirect(url_for('main.index'))
            else:
                flash('Invalid password.', 'error')
    
    return render_template('fallback_login.html')
