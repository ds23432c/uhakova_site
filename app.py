import os
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from config import Config
from models import db, User

login_manager = LoginManager()
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(os.path.join(app.root_path, 'static', 'uploads'), exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    Migrate(app, db)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Пожалуйста, войдите в систему'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from routes.auth import auth_bp
    from routes.lessons import lessons_bp
    from routes.tests import tests_bp
    from routes.profile import profile_bp
    from routes.admin import admin_bp
    from routes.main import main_bp
    from routes.forum import forum_bp
    from routes.blog import blog_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(lessons_bp)
    app.register_blueprint(tests_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(forum_bp)
    app.register_blueprint(blog_bp)

    with app.app_context():
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        if not inspector.has_table('users'):
            print("📦 Создаём таблицы базы данных...")
            db.create_all()
            from seed_data import seed_database
            seed_database()
        else:
            print("✅ База данных уже существует, пропускаем инициализацию")

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
