from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required, current_user
from functools import wraps
from models import db, User, Module, Lesson, Question, BlogPost, Feedback, TestResult, Progress, AdminLog
from datetime import datetime
import io

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Доступ запрещён', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    users_count = User.query.filter_by(role='user').count()
    lessons_count = Lesson.query.count()
    completed_count = Progress.query.filter_by(completed=True).count()
    feedback_count = Feedback.query.filter_by(is_read=False).count()

    # Последние пользователи
    recent_users = User.query.filter_by(role='user').order_by(User.created_at.desc()).limit(5).all()
    # Последние результаты тестов
    recent_tests = TestResult.query.order_by(TestResult.taken_at.desc()).limit(5).all()

    return render_template('admin/dashboard.html',
        users_count=users_count,
        lessons_count=lessons_count,
        completed_count=completed_count,
        feedback_count=feedback_count,
        recent_users=recent_users,
        recent_tests=recent_tests
    )


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    all_users = User.query.filter_by(role='user').order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users)


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active_user = not user.is_active_user
    db.session.commit()
    status = 'активирован' if user.is_active_user else 'заблокирован'
    flash(f'Пользователь {user.name} {status}', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/lessons')
@login_required
@admin_required
def lessons():
    modules = Module.query.order_by(Module.order_num).all()
    return render_template('admin/lessons.html', modules=modules)


@admin_bp.route('/lessons/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_lesson():
    modules = Module.query.order_by(Module.order_num).all()
    if request.method == 'POST':
        module_id = request.form.get('module_id')
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        duration = request.form.get('duration_min', 10)
        order_num = request.form.get('order_num', 1)
        if title and content and module_id:
            lesson = Lesson(module_id=module_id, title=title, content=content, duration_min=int(duration), order_num=int(order_num))
            db.session.add(lesson)
            log = AdminLog(admin_id=current_user.id, action=f'Добавил урок: {title}')
            db.session.add(log)
            db.session.commit()
            flash('Урок добавлен!', 'success')
            return redirect(url_for('admin.lessons'))
    return render_template('admin/add_lesson.html', modules=modules)


@admin_bp.route('/lessons/<int:lesson_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    modules = Module.query.order_by(Module.order_num).all()
    if request.method == 'POST':
        lesson.title = request.form.get('title', lesson.title)
        lesson.content = request.form.get('content', lesson.content)
        lesson.duration_min = int(request.form.get('duration_min', lesson.duration_min))
        lesson.module_id = int(request.form.get('module_id', lesson.module_id))
        db.session.commit()
        flash('Урок обновлён!', 'success')
        return redirect(url_for('admin.lessons'))
    return render_template('admin/edit_lesson.html', lesson=lesson, modules=modules)


@admin_bp.route('/lessons/<int:lesson_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    title = lesson.title
    db.session.delete(lesson)
    log = AdminLog(admin_id=current_user.id, action=f'Удалил урок: {title}')
    db.session.add(log)
    db.session.commit()
    flash(f'Урок "{title}" удалён', 'success')
    return redirect(url_for('admin.lessons'))


@admin_bp.route('/feedback')
@login_required
@admin_required
def feedback():
    items = Feedback.query.order_by(Feedback.created_at.desc()).all()
    for f in items:
        f.is_read = True
    db.session.commit()
    return render_template('admin/feedback.html', items=items)


@admin_bp.route('/blog')
@login_required
@admin_required
def blog():
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('admin/blog.html', posts=posts)


@admin_bp.route('/blog/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_post():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        if title and content:
            post = BlogPost(title=title, content=content, is_published=True)
            db.session.add(post)
            db.session.commit()
            flash('Статья опубликована!', 'success')
            return redirect(url_for('admin.blog'))
    return render_template('admin/add_post.html')


@admin_bp.route('/email', methods=['GET', 'POST'])
@login_required
@admin_required
def send_email():
    if request.method == 'POST':
        subject = request.form.get('subject', '')
        message = request.form.get('message', '')
        flash(f'Рассылка отправлена всем пользователям (тема: {subject})', 'success')
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/email.html')


@admin_bp.route('/export/users')
@login_required
@admin_required
def export_users():
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Пользователи'

        headers = ['ID', 'Имя', 'Email', 'Возраст', 'Город', 'Дата регистрации', 'Активен']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color='2c5f8a', end_color='2c5f8a', fill_type='solid')
            cell.font = Font(bold=True, color='FFFFFF')

        users = User.query.filter_by(role='user').all()
        for row, user in enumerate(users, 2):
            ws.cell(row=row, column=1, value=user.id)
            ws.cell(row=row, column=2, value=user.name)
            ws.cell(row=row, column=3, value=user.email)
            ws.cell(row=row, column=4, value=user.age)
            ws.cell(row=row, column=5, value=user.city)
            ws.cell(row=row, column=6, value=user.created_at.strftime('%d.%m.%Y') if user.created_at else '')
            ws.cell(row=row, column=7, value='Да' if user.is_active_user else 'Нет')

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name='users.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        flash(f'Ошибка экспорта: {str(e)}', 'danger')
        return redirect(url_for('admin.users'))
