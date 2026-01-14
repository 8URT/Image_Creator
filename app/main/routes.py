from flask import render_template, redirect, url_for, request
from flask_login import login_required, current_user
from app.main import bp
from app.models import UsageLog
from app import db
from datetime import datetime

@bp.route('/')
def index():
    """Home page - redirect to tools if logged in"""
    if current_user.is_authenticated:
        return redirect(url_for('main.tools'))
    return redirect(url_for('auth.login'))

@bp.route('/tools')
@login_required
def tools():
    """Tools dashboard"""
    return render_template('tools/index.html')

@bp.route('/tools/image_creator')
@login_required
def image_creator():
    """Social Image Creator tool"""
    from app.models import TemplateConfig
    config = TemplateConfig.query.filter_by(tool_name='image_creator').first()
    config_dict = config.get_config() if config else {}
    
    # Log usage
    log_usage('image_creator')
    
    return render_template('tools/image_creator.html', template_config=config_dict)

@bp.route('/tools/bulk')
@login_required
def bulk():
    """Bulk Watermarker tool"""
    from app.models import TemplateConfig
    config = TemplateConfig.query.filter_by(tool_name='bulk').first()
    config_dict = config.get_config() if config else {}
    
    log_usage('bulk')
    
    return render_template('tools/bulk.html', template_config=config_dict)

@bp.route('/tools/quote_creator')
@login_required
def quote_creator():
    """Quote Image Creator tool"""
    from app.models import TemplateConfig
    config = TemplateConfig.query.filter_by(tool_name='quote_creator').first()
    config_dict = config.get_config() if config else {}
    
    log_usage('quote_creator')
    
    return render_template('tools/quote_creator.html', template_config=config_dict)

@bp.route('/tools/watermarker')
@login_required
def watermarker():
    """Photo Watermarker tool"""
    from app.models import TemplateConfig
    config = TemplateConfig.query.filter_by(tool_name='watermarker').first()
    config_dict = config.get_config() if config else {}
    
    log_usage('watermarker')
    
    return render_template('tools/watermarker.html', template_config=config_dict)

@bp.route('/tools/watermarker_1')
@login_required
def watermarker_1():
    """Watermarker LM + Overlay tool"""
    from app.models import TemplateConfig
    config = TemplateConfig.query.filter_by(tool_name='watermarker_1').first()
    config_dict = config.get_config() if config else {}
    
    log_usage('watermarker_1')
    
    return render_template('tools/watermarker_1.html', template_config=config_dict)

@bp.route('/tools/mindvalley')
@login_required
def mindvalley():
    """Long Title Creator tool"""
    from app.models import TemplateConfig
    config = TemplateConfig.query.filter_by(tool_name='mindvalley').first()
    config_dict = config.get_config() if config else {}
    
    log_usage('mindvalley')
    
    return render_template('tools/mindvalley.html', template_config=config_dict)

@bp.route('/tools/turf_magazine')
@login_required
def turf_magazine():
    """Turf Magazine Image Creator tool"""
    from app.models import TemplateConfig
    config = TemplateConfig.query.filter_by(tool_name='turf_magazine').first()
    config_dict = config.get_config() if config else {}
    
    log_usage('turf_magazine')
    
    return render_template('tools/turf_magazine.html', template_config=config_dict)

@bp.route('/tools/turf_magazine_bulk')
@login_required
def turf_magazine_bulk():
    """Turf Magazine Bulk Watermarking tool"""
    from app.models import TemplateConfig
    config = TemplateConfig.query.filter_by(tool_name='turf_magazine_bulk').first()
    config_dict = config.get_config() if config else {}
    
    log_usage('turf_magazine_bulk')
    
    return render_template('tools/turf_magazine_bulk.html', template_config=config_dict)

def log_usage(tool_name):
    """Log tool usage"""
    try:
        log = UsageLog(
            user_id=current_user.id,
            tool_name=tool_name,
            timestamp=datetime.utcnow(),
            ip_address=request.remote_addr if request else None
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        # Don't fail if logging fails
        db.session.rollback()
        pass
