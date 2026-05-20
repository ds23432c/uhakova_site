from flask import Blueprint, render_template, request, jsonify
from models import Module, Lesson, GlossaryTerm, FAQ, BlogPost, Feedback, db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    modules = Module.query.order_by(Module.order_num).all()
    blog_posts = BlogPost.query.filter_by(is_published=True).order_by(BlogPost.created_at.desc()).limit(3).all()
    return render_template('index.html', modules=modules, blog_posts=blog_posts)

@main_bp.route('/glossary')
def glossary():
    terms = GlossaryTerm.query.order_by(GlossaryTerm.term).all()
    letters = sorted(set(t.letter for t in terms if t.letter))
    return render_template('glossary.html', terms=terms, letters=letters)

@main_bp.route('/faq')
def faq():
    faqs = FAQ.query.order_by(FAQ.order_num).all()
    return render_template('faq.html', faqs=faqs)

@main_bp.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()
        if message:
            fb = Feedback(name=name, email=email, message=message)
            db.session.add(fb)
            db.session.commit()
            from flask import flash
            flash('Ваше сообщение отправлено! Мы ответим вам в ближайшее время.', 'success')
            from flask import redirect, url_for
            return redirect(url_for('main.feedback'))
    return render_template('feedback.html')

@main_bp.route('/search')
def search():
    query = request.args.get('q', '').strip()
    lessons = []
    terms = []
    if query:
        lessons = Lesson.query.filter(
            Lesson.title.ilike(f'%{query}%') | Lesson.content.ilike(f'%{query}%')
        ).all()
        terms = GlossaryTerm.query.filter(
            GlossaryTerm.term.ilike(f'%{query}%') | GlossaryTerm.definition.ilike(f'%{query}%')
        ).all()
    return render_template('search.html', query=query, lessons=lessons, terms=terms)
