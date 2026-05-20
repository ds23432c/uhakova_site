from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, ForumTopic, ForumReply

forum_bp = Blueprint('forum', __name__)

@forum_bp.route('/forum')
def forum():
    topics = ForumTopic.query.order_by(ForumTopic.is_pinned.desc(), ForumTopic.created_at.desc()).all()
    return render_template('forum/forum.html', topics=topics)

@forum_bp.route('/forum/new', methods=['GET', 'POST'])
@login_required
def new_topic():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        text = request.form.get('text', '').strip()
        if title and text:
            topic = ForumTopic(user_id=current_user.id, title=title, text=text)
            db.session.add(topic)
            db.session.commit()
            flash('Тема создана!', 'success')
            return redirect(url_for('forum.topic', topic_id=topic.id))
        flash('Заполните все поля', 'danger')
    return render_template('forum/new_topic.html')

@forum_bp.route('/forum/<int:topic_id>', methods=['GET', 'POST'])
def topic(topic_id):
    topic = ForumTopic.query.get_or_404(topic_id)
    topic.views += 1
    db.session.commit()
    if request.method == 'POST':
        if not current_user.is_authenticated:
            flash('Войдите чтобы ответить', 'warning')
            return redirect(url_for('auth.login'))
        text = request.form.get('text', '').strip()
        if text:
            reply = ForumReply(topic_id=topic_id, user_id=current_user.id, text=text)
            db.session.add(reply)
            db.session.commit()
            flash('Ответ добавлен', 'success')
        return redirect(url_for('forum.topic', topic_id=topic_id))
    return render_template('forum/topic.html', topic=topic)
