from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
import os
from werkzeug.utils import secure_filename

auth_bp = Blueprint('auth', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        age = request.form.get('age', '')
        city = request.form.get('city', '').strip()

        if not name or not email or not password:
            flash('Заполните все обязательные поля', 'danger')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('Пользователь с таким email уже существует', 'danger')
            return render_template('auth/register.html')

        if len(password) < 6:
            flash('Пароль должен содержать не менее 6 символов', 'danger')
            return render_template('auth/register.html')

        user = User(name=name, email=email, city=city)
        if age:
            try:
                user.age = int(age)
            except:
                pass
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash(f'Добро пожаловать, {name}! Ваш аккаунт создан.', 'success')
        return redirect(url_for('main.index'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            if not user.is_active_user:
                flash('Ваш аккаунт заблокирован. Обратитесь к администратору.', 'danger')
                return render_template('auth/login.html')
            login_user(user, remember=remember)
            from datetime import datetime, date
            user.last_seen = datetime.utcnow()
            db.session.commit()
            next_page = request.args.get('next')
            flash(f'С возвращением, {user.name}!', 'success')
            return redirect(next_page or url_for('main.index'))
        else:
            flash('Неверный email или пароль', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()
        flash('Если такой email зарегистрирован, мы отправим инструкции по восстановлению пароля.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/forgot_password.html')
