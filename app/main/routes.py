from flask import render_template, redirect, url_for, request, send_from_directory, abort
from flask_login import login_required, current_user
from app.main import bp
from app.models import UsageLog
from app import db
from app.budget_catalog import BUDGET_ROOT, load_budget_catalog, is_allowed_budget_media_path
from datetime import datetime

@bp.route('/')
def index():
    """Home page - redirect to image creator if logged in"""
    if current_user.is_authenticated:
        return redirect(url_for('main.image_creator'))
    return redirect(url_for('auth.login'))

@bp.route('/image_creator')
@login_required
def image_creator():
    """Social Image Creator tool"""
    from app.models import TemplateConfig
    config = TemplateConfig.query.filter_by(tool_name='image_creator').first()
    config_dict = config.get_config() if config else {}
    
    # Log usage
    log_usage('image_creator')
    
    return render_template('tools/image_creator.html', template_config=config_dict)

@bp.route('/turf_creator')
@login_required
def turf_creator():
    """Turf Magazine Image Creator tool (Turf logo top-right)"""
    from app.models import TemplateConfig
    config = TemplateConfig.query.filter_by(tool_name='image_creator').first()
    config_dict = config.get_config() if config else {}

    log_usage('turf_creator')

    return render_template('tools/image_creator.html', template_config=config_dict, force_turf_top_right=True)

@bp.route('/budget_creator')
@login_required
def budget_creator():
    """Budget Speech 2026-2027 Image Creator with themed illustrations"""
    from app.models import TemplateConfig
    config = TemplateConfig.query.filter_by(tool_name='image_creator').first()
    config_dict = config.get_config() if config else {}

    log_usage('budget_creator')

    return render_template(
        'tools/image_creator.html',
        template_config=config_dict,
        budget_mode=True,
        budget_themes=load_budget_catalog(),
    )

@bp.route('/budget-media/<path:subpath>')
@login_required
def budget_media(subpath):
    """Serve standardized budget speech images (login required)."""
    if not is_allowed_budget_media_path(subpath):
        abort(404)
    return send_from_directory(BUDGET_ROOT, subpath)

@bp.route('/layout_creator')
@login_required
def layout_creator():
    """Layout Creator tool"""
    from app.models import TemplateConfig
    config = TemplateConfig.query.filter_by(tool_name='layout_creator').first()
    config_dict = config.get_config() if config else {}
    
    # Log usage
    log_usage('layout_creator')
    
    return render_template('tools/layout_creator.html', template_config=config_dict)

@bp.route('/carousel_creator')
@login_required
def carousel_creator():
    """Carousel Creator tool"""
    from app.models import TemplateConfig
    config = TemplateConfig.query.filter_by(tool_name='carousel_creator').first()
    config_dict = config.get_config() if config else {}

    # Log usage
    log_usage('carousel_creator')

    return render_template('tools/carousel_creator.html', template_config=config_dict)

# Backwards-compatible aliases (avoid 404s from old/guessed URLs)
@bp.route('/carousel')
@bp.route('/tools/carousel_creator')
@bp.route('/tools/carousel')
@login_required
def carousel_creator_alias():
    return redirect(url_for('main.carousel_creator'))

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
