from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app.admin import bp
from app.admin.decorators import admin_required
from app.admin.forms import UserForm, TemplateConfigForm
from app.models import User, TemplateConfig, UsageLog
from app import db
from app.config import Config
from datetime import datetime, timedelta
import json

@bp.route('/')
@login_required
@admin_required
def dashboard():
    """Admin dashboard"""
    # Statistics
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    admin_users = User.query.filter_by(is_admin=True).count()
    
    # Recent activity (last 24 hours)
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_logs = UsageLog.query.filter(UsageLog.timestamp >= yesterday).order_by(UsageLog.timestamp.desc()).limit(10).all()
    
    # Tool usage stats
    tool_stats = db.session.query(
        UsageLog.tool_name,
        db.func.count(UsageLog.id).label('count')
    ).filter(UsageLog.timestamp >= yesterday).group_by(UsageLog.tool_name).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         active_users=active_users,
                         admin_users=admin_users,
                         recent_logs=recent_logs,
                         tool_stats=tool_stats)

@bp.route('/users')
@login_required
@admin_required
def users():
    """User management page"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    filter_admin = request.args.get('filter_admin', '', type=str)
    filter_active = request.args.get('filter_active', '', type=str)
    
    query = User.query
    
    # Apply filters
    if search:
        query = query.filter(
            (User.email.contains(search)) |
            (User.username.contains(search))
        )
    if filter_admin == 'true':
        query = query.filter_by(is_admin=True)
    elif filter_admin == 'false':
        query = query.filter_by(is_admin=False)
    if filter_active == 'true':
        query = query.filter_by(is_active=True)
    elif filter_active == 'false':
        query = query.filter_by(is_active=False)
    
    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/users.html',
                         users=pagination.items,
                         pagination=pagination,
                         search=search,
                         filter_admin=filter_admin,
                         filter_active=filter_active)

@bp.route('/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    """Add new user"""
    form = UserForm()
    
    if request.method == 'POST':
        if not form.validate():
            # Form validation failed - show errors
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{field}: {error}', 'error')
            return render_template('admin/user_form.html', form=form, title='Add User')
    
    if form.validate_on_submit():
        # Check if email already exists (additional check)
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email already registered.', 'error')
            return render_template('admin/user_form.html', form=form, title='Add User')
        
        # Check if username already exists (if provided)
        username = None
        if form.username.data and form.username.data.strip():
            username = form.username.data.strip()
            existing_username = User.query.filter_by(username=username).first()
            if existing_username:
                flash('Username already taken.', 'error')
                return render_template('admin/user_form.html', form=form, title='Add User')
        
        try:
            # If Google OAuth user is selected, ensure password is empty
            password_hash = None
            if form.password.data and not form.is_google_user.data:
                password_hash = generate_password_hash(form.password.data)
            elif form.password.data and form.is_google_user.data:
                flash('Google OAuth users should not have a password. Password field will be ignored.', 'warning')
            
            user = User(
                email=form.email.data,
                username=username,  # Will be None if not provided or empty
                password_hash=password_hash,
                is_admin=form.is_admin.data if form.is_admin.data else False,
                is_active=form.is_active.data if form.is_active.data is not None else True
            )
            
            db.session.add(user)
            db.session.commit()
            
            auth_method = "Google OAuth" if form.is_google_user.data else "Password"
            flash(f'User {user.email} created successfully. Auth method: {auth_method}.', 'success')
            if form.is_google_user.data:
                flash('Note: User will need to log in with Google OAuth to link their Google account.', 'info')
            return redirect(url_for('admin.users'))
        except Exception as e:
            db.session.rollback()
            import traceback
            import logging
            error_msg = str(e)
            logging.error(f'Error creating user: {error_msg}', exc_info=True)
            logging.error(f'Traceback: {traceback.format_exc()}')
            # Show detailed error in development
            if hasattr(Config, 'FLASK_ENV') and Config.FLASK_ENV == 'development':
                flash(f'Error creating user: {error_msg}', 'error')
            else:
                flash('Error creating user. Please check the logs.', 'error')
            return render_template('admin/user_form.html', form=form, title='Add User')
    
    return render_template('admin/user_form.html', form=form, title='Add User')

@bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit user"""
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    form._user_id = user_id  # For validation
    
    # Set is_google_user based on whether user has google_id
    if user.google_id:
        form.is_google_user.data = True
    
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data.strip() if form.username.data and form.username.data.strip() else None
        
        # Handle password - if Google OAuth user, don't set password
        if form.is_google_user.data:
            # Clear password for Google OAuth users
            if form.password.data:
                flash('Google OAuth users should not have a password. Password field will be ignored.', 'warning')
            user.password_hash = None
        elif form.password.data:
            # Set password for non-Google users
            user.password_hash = generate_password_hash(form.password.data)
        # If password is empty and not Google user, keep existing password (don't change it)
        
        user.is_admin = form.is_admin.data if form.is_admin.data else False
        user.is_active = form.is_active.data if form.is_active.data is not None else True
        
        db.session.commit()
        
        auth_method = "Google OAuth" if form.is_google_user.data else ("Password" if user.password_hash else "No password set")
        flash(f'User {user.email} updated successfully. Auth method: {auth_method}.', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/user_form.html', form=form, user=user, title='Edit User')

@bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete user"""
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting yourself
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin.users'))
    
    email = user.email
    db.session.delete(user)
    db.session.commit()
    flash(f'User {email} deleted successfully.', 'success')
    return redirect(url_for('admin.users'))

@bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    """Toggle user active status"""
    user = User.query.get_or_404(user_id)
    
    # Prevent disabling yourself
    if user.id == current_user.id:
        flash('You cannot disable your own account.', 'error')
        return redirect(url_for('admin.users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    status = 'enabled' if user.is_active else 'disabled'
    flash(f'User {user.email} {status} successfully.', 'success')
    return redirect(url_for('admin.users'))

@bp.route('/templates')
@login_required
@admin_required
def templates():
    """Template management page"""
    tool_configs = {}
    # Only image_creator is active - other tools archived and integrated into image_creator
    tool_names = ['image_creator']
    
    for tool_name in tool_names:
        config = TemplateConfig.query.filter_by(tool_name=tool_name).first()
        if config:
            tool_configs[tool_name] = config.get_config()
        else:
            # Default config
            tool_configs[tool_name] = get_default_template_config(tool_name)
    
    return render_template('admin/templates.html', tool_configs=tool_configs, tool_names=tool_names)

@bp.route('/templates/<tool_name>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_template(tool_name):
    """Edit template configuration"""
    config = TemplateConfig.query.filter_by(tool_name=tool_name).first()
    
    if request.method == 'POST':
        try:
            config_json = request.get_json() or {}
            
            if config:
                config.set_config(config_json)
                config.updated_by = current_user.id
                config.updated_at = datetime.utcnow()
            else:
                config = TemplateConfig(
                    tool_name=tool_name,
                    config_json=json.dumps(config_json),
                    updated_by=current_user.id
                )
                db.session.add(config)
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Template configuration saved.'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 400
    
    # GET request - return current config
    if config:
        config_dict = config.get_config()
    else:
        config_dict = get_default_template_config(tool_name)
    
    return jsonify(config_dict)

@bp.route('/logs')
@login_required
@admin_required
def logs():
    """Usage logs page"""
    page = request.args.get('page', 1, type=int)
    search_user = request.args.get('search_user', '', type=str)
    filter_tool = request.args.get('filter_tool', '', type=str)
    date_from = request.args.get('date_from', '', type=str)
    date_to = request.args.get('date_to', '', type=str)
    
    query = UsageLog.query
    
    # Apply filters
    if search_user:
        query = query.join(User).filter(
            (User.email.contains(search_user)) |
            (User.username.contains(search_user))
        )
    if filter_tool:
        query = query.filter_by(tool_name=filter_tool)
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(UsageLog.timestamp >= date_from_obj)
        except ValueError:
            pass
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            query = query.filter(UsageLog.timestamp <= date_to_obj)
        except ValueError:
            pass
    
    pagination = query.order_by(UsageLog.timestamp.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    
    # Get unique tool names for filter
    tool_names = db.session.query(UsageLog.tool_name).distinct().all()
    tool_names = [t[0] for t in tool_names]
    
    return render_template('admin/logs.html',
                         logs=pagination.items,
                         pagination=pagination,
                         search_user=search_user,
                         filter_tool=filter_tool,
                         date_from=date_from,
                         date_to=date_to,
                         tool_names=tool_names)

def get_default_template_config(tool_name):
    """Get default template configuration for a tool"""
    defaults = {
        'image_creator': {
            'fonts': {
                'default_family': 'Fira Sans',
                'available_families': ['Fira Sans', 'Parkinsans', 'Barlow Condensed'],
                'title_weight': '800',
                'subtitle_weight': '700',
                'title_size': {'min': 36, 'max': 140, 'default': 120},
                'subtitle_size': {'min': 20, 'max': 80, 'default': 50}
            },
            'layout': {
                'canvas_width': 1000,
                'canvas_height': 1250,
                'text_placements': ['Top Left', 'Bottom Left', 'Top Center', 'Bottom Center']
            },
            'colors': {
                'subtitle_default': '#FFFFFF',
                'subtitle_background_default': '#DD3333',
                'background_default': '#000000'
            }
        },
        'bulk': {
            'fonts': {},
            'layout': {
                'max_dimension_original': 2000,
                'max_dimension_compressed': 1920,
                'compression_quality': 0.7
            }
        },
        'quote_creator': {
            'fonts': {
                'default_family': 'Playfair',
                'available_families': ['Fira Sans', 'Parkinsans', 'Barlow Condensed', 'Playfair'],
                'quote_weight': '900',
                'name_weight': '900',
                'quote_size': {'min': 36, 'max': 120, 'default': 80},
                'name_size': {'min': 20, 'max': 80, 'default': 50}
            },
            'layout': {
                'canvas_width': 1000,
                'canvas_height': 1250
            }
        }
    }
    
    return defaults.get(tool_name, {})
