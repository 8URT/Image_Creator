from flask import render_template, redirect, url_for, request
from flask_login import login_required, current_user
from app.main import bp
from app.models import UsageLog
from app import db
from datetime import datetime

@bp.route('/')
def index():
    """Home page - redirect to image creator if logged in"""
    if current_user.is_authenticated:
        return redirect(url_for('main.image_creator'))
    return redirect(url_for('auth.login'))

@bp.route('/image_creator')
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

# Archived tool routes - functionality integrated into image_creator
# @bp.route('/tools/bulk')
# @login_required
# def bulk():
#     """Bulk Watermarker tool - ARCHIVED: Now integrated into image_creator"""
#     pass

# @bp.route('/tools/quote_creator')
# @login_required
# def quote_creator():
#     """Quote Image Creator tool - ARCHIVED: Now integrated into image_creator"""
#     pass

# @bp.route('/tools/watermarker')
# @login_required
# def watermarker():
#     """Photo Watermarker tool - ARCHIVED"""
#     pass

# @bp.route('/tools/watermarker_1')
# @login_required
# def watermarker_1():
#     """Watermarker LM + Overlay tool - ARCHIVED"""
#     pass

# @bp.route('/tools/mindvalley')
# @login_required
# def mindvalley():
#     """Long Title Creator tool - ARCHIVED"""
#     pass

# @bp.route('/tools/turf_magazine')
# @login_required
# def turf_magazine():
#     """Turf Magazine Image Creator tool - ARCHIVED"""
#     pass

# @bp.route('/tools/turf_magazine_bulk')
# @login_required
# def turf_magazine_bulk():
#     """Turf Magazine Bulk Watermarking tool - ARCHIVED"""
#     pass

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
