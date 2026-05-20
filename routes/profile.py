from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required, current_user
from models import db, User, Progress, TestResult, UserBadge, Bookmark, Note, Notification, ActivityLog, Module, Lesson
from datetime import datetime, date
import os, io

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile')
@login_required
def profile():
    modules = Module.query.order_by(Module.order_num).all()
    completed_ids = {p.lesson_id for p in current_user.progress if p.completed}
    total_lessons = Lesson.query.count()
    completed_count = len(completed_ids)
    percent = int((completed_count / total_lessons) * 100) if total_lessons > 0 else 0

    test_results = TestResult.query.filter_by(user_id=current_user.id).order_by(TestResult.taken_at.desc()).limit(10).all()
    badges = UserBadge.query.filter_by(user_id=current_user.id).all()
    bookmarks = Bookmark.query.filter_by(user_id=current_user.id).all()
    unread_notifs = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()

    level_name, level_num = current_user.get_level()
    xp = current_user.get_total_xp()

    return render_template('profile/profile.html',
        modules=modules,
        completed_ids=completed_ids,
        completed_count=completed_count,
        total_lessons=total_lessons,
        percent=percent,
        test_results=test_results,
        badges=badges,
        bookmarks=bookmarks,
        unread_notifs=unread_notifs,
        level_name=level_name,
        level_num=level_num,
        xp=xp
    )


@profile_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.name = request.form.get('name', '').strip() or current_user.name
        current_user.city = request.form.get('city', '').strip()
        age = request.form.get('age', '')
        if age:
            try:
                current_user.age = int(age)
            except:
                pass

        # Аватар
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and file.filename:
                from werkzeug.utils import secure_filename
                ext = file.filename.rsplit('.', 1)[-1].lower()
                if ext in {'png', 'jpg', 'jpeg', 'gif'}:
                    filename = f'avatar_{current_user.id}.{ext}'
                    upload_path = os.path.join('static', 'uploads', filename)
                    file.save(upload_path)
                    current_user.avatar = filename

        db.session.commit()
        flash('Профиль обновлён!', 'success')
        return redirect(url_for('profile.profile'))

    return render_template('profile/edit.html')


@profile_bp.route('/profile/badges')
@login_required
def badges():
    from models import Badge
    all_badges = Badge.query.all()
    earned_ids = {ub.badge_id for ub in current_user.user_badges}
    return render_template('profile/badges.html', all_badges=all_badges, earned_ids=earned_ids)


@profile_bp.route('/profile/activity')
@login_required
def activity():
    logs = ActivityLog.query.filter_by(user_id=current_user.id).order_by(ActivityLog.created_at.desc()).limit(50).all()
    return render_template('profile/activity.html', logs=logs)


@profile_bp.route('/profile/notifications')
@login_required
def notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    for n in notifs:
        n.is_read = True
    db.session.commit()
    return render_template('profile/notifications.html', notifs=notifs)


@profile_bp.route('/profile/certificate')
@login_required
def certificate():
    total_lessons = Lesson.query.count()
    completed_count = Progress.query.filter_by(user_id=current_user.id, completed=True).count()
    if completed_count < total_lessons:
        flash(f'Для получения сертификата нужно пройти все уроки. Пройдено: {completed_count}/{total_lessons}', 'warning')
        return redirect(url_for('profile.profile'))
    return render_template('profile/certificate.html', user=current_user)


@profile_bp.route('/profile/certificate/download')
@login_required
def download_certificate():
    total_lessons = Lesson.query.count()
    completed_count = Progress.query.filter_by(user_id=current_user.id, completed=True).count()
    if completed_count < total_lessons:
        flash('Сначала завершите все уроки', 'warning')
        return redirect(url_for('profile.profile'))

    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle('title', fontSize=28, alignment=1, spaceAfter=20, textColor=colors.HexColor('#2c5f8a'), fontName='Helvetica-Bold')
        subtitle_style = ParagraphStyle('subtitle', fontSize=16, alignment=1, spaceAfter=10, textColor=colors.HexColor('#555'))
        name_style = ParagraphStyle('name', fontSize=24, alignment=1, spaceAfter=20, textColor=colors.HexColor('#1a1a1a'), fontName='Helvetica-Bold')
        body_style = ParagraphStyle('body', fontSize=14, alignment=1, spaceAfter=10, textColor=colors.HexColor('#333'))
        date_style = ParagraphStyle('date', fontSize=12, alignment=2, textColor=colors.HexColor('#888'))

        story = [
            Spacer(1, 1*cm),
            Paragraph('🎓 СЕРТИФИКАТ', title_style),
            Paragraph('об успешном прохождении курса', subtitle_style),
            Paragraph('"Компьютерная грамотность для пожилых людей"', subtitle_style),
            Spacer(1, 0.5*cm),
            Paragraph('Настоящим подтверждается, что', body_style),
            Paragraph(current_user.name, name_style),
            Paragraph('успешно прошёл(а) все 5 модулей курса и набрал(а) необходимое количество баллов.', body_style),
            Spacer(1, 1*cm),
            Paragraph(f'Дата выдачи: {datetime.utcnow().strftime("%d.%m.%Y")}', date_style),
        ]

        doc.build(story)
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name='certificate.pdf', mimetype='application/pdf')
    except Exception as e:
        flash(f'Ошибка генерации сертификата: {str(e)}', 'danger')
        return redirect(url_for('profile.certificate'))
