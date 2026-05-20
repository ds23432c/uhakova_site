from flask import Blueprint, render_template, redirect, url_for, flash, request, make_response
from flask_login import login_required, current_user
from models import db, Module, Lesson, Progress, Bookmark, Note, Comment, ActivityLog, Notification
from datetime import datetime

lessons_bp = Blueprint('lessons', __name__)

@lessons_bp.route('/lessons')
def lessons_list():
    modules = Module.query.order_by(Module.order_num).all()
    user_progress = {}
    if current_user.is_authenticated:
        progress = Progress.query.filter_by(user_id=current_user.id, completed=True).all()
        user_progress = {p.lesson_id for p in progress}
    return render_template('lessons/list.html', modules=modules, user_progress=user_progress)


@lessons_bp.route('/lesson/<int:lesson_id>')
def lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    is_bookmarked = False
    user_note = None
    comments = Comment.query.filter_by(lesson_id=lesson_id).order_by(Comment.created_at.desc()).all()
    is_completed = False

    if current_user.is_authenticated:
        bm = Bookmark.query.filter_by(user_id=current_user.id, lesson_id=lesson_id).first()
        is_bookmarked = bm is not None
        note = Note.query.filter_by(user_id=current_user.id, lesson_id=lesson_id).first()
        user_note = note.text if note else ''
        prog = Progress.query.filter_by(user_id=current_user.id, lesson_id=lesson_id).first()
        is_completed = prog.completed if prog else False

        log = ActivityLog(user_id=current_user.id, action=f'Открыл урок: {lesson.title}', date=datetime.utcnow().date())
        db.session.add(log)
        db.session.commit()

    prev_lesson = Lesson.query.filter_by(module_id=lesson.module_id).filter(Lesson.order_num < lesson.order_num).order_by(Lesson.order_num.desc()).first()
    next_lesson = Lesson.query.filter_by(module_id=lesson.module_id).filter(Lesson.order_num > lesson.order_num).order_by(Lesson.order_num.asc()).first()

    return render_template('lessons/lesson.html',
        lesson=lesson,
        is_bookmarked=is_bookmarked,
        user_note=user_note,
        comments=comments,
        is_completed=is_completed,
        prev_lesson=prev_lesson,
        next_lesson=next_lesson
    )


@lessons_bp.route('/lesson/<int:lesson_id>/complete', methods=['POST'])
@login_required
def complete_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    prog = Progress.query.filter_by(user_id=current_user.id, lesson_id=lesson_id).first()
    if not prog:
        prog = Progress(user_id=current_user.id, lesson_id=lesson_id)
        db.session.add(prog)
    if not prog.completed:
        prog.completed = True
        prog.xp_earned = 20
        prog.completed_at = datetime.utcnow()
        notif = Notification(user_id=current_user.id, text=f'✅ Урок "{lesson.title}" завершён! +20 XP', link=url_for('lessons.lesson', lesson_id=lesson_id))
        db.session.add(notif)
        _check_badges(current_user)
    db.session.commit()
    flash('Урок отмечен как завершённый! +20 XP', 'success')
    return redirect(url_for('lessons.lesson', lesson_id=lesson_id))


@lessons_bp.route('/lesson/<int:lesson_id>/bookmark', methods=['POST'])
@login_required
def toggle_bookmark(lesson_id):
    bm = Bookmark.query.filter_by(user_id=current_user.id, lesson_id=lesson_id).first()
    if bm:
        db.session.delete(bm)
        flash('Закладка удалена', 'info')
    else:
        db.session.add(Bookmark(user_id=current_user.id, lesson_id=lesson_id))
        flash('Урок добавлен в закладки', 'success')
    db.session.commit()
    return redirect(url_for('lessons.lesson', lesson_id=lesson_id))


@lessons_bp.route('/lesson/<int:lesson_id>/note', methods=['POST'])
@login_required
def save_note(lesson_id):
    text = request.form.get('note_text', '').strip()
    note = Note.query.filter_by(user_id=current_user.id, lesson_id=lesson_id).first()
    if note:
        note.text = text
        note.updated_at = datetime.utcnow()
    else:
        note = Note(user_id=current_user.id, lesson_id=lesson_id, text=text)
        db.session.add(note)
    db.session.commit()
    flash('Заметка сохранена', 'success')
    return redirect(url_for('lessons.lesson', lesson_id=lesson_id))


@lessons_bp.route('/lesson/<int:lesson_id>/comment', methods=['POST'])
@login_required
def add_comment(lesson_id):
    text = request.form.get('comment_text', '').strip()
    if text:
        comment = Comment(user_id=current_user.id, lesson_id=lesson_id, text=text)
        db.session.add(comment)
        db.session.commit()
        flash('Комментарий добавлен', 'success')
    return redirect(url_for('lessons.lesson', lesson_id=lesson_id))


@lessons_bp.route('/lesson/<int:lesson_id>/print')
def print_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    return render_template('lessons/print.html', lesson=lesson)


def _check_badges(user):
    from models import Badge, UserBadge
    completed_count = Progress.query.filter_by(user_id=user.id, completed=True).count()
    badges = Badge.query.filter_by(condition_type='lessons_count').all()
    for badge in badges:
        if completed_count >= badge.condition_value:
            existing = UserBadge.query.filter_by(user_id=user.id, badge_id=badge.id).first()
            if not existing:
                db.session.add(UserBadge(user_id=user.id, badge_id=badge.id))
                notif = Notification(user_id=user.id, text=f'🏆 Получен бейдж: {badge.icon} {badge.name}!')
                db.session.add(notif)
