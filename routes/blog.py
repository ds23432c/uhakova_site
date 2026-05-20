from flask import Blueprint, render_template
from models import BlogPost

blog_bp = Blueprint('blog', __name__)

@blog_bp.route('/blog')
def blog():
    posts = BlogPost.query.filter_by(is_published=True).order_by(BlogPost.created_at.desc()).all()
    return render_template('blog/blog.html', posts=posts)

@blog_bp.route('/blog/<int:post_id>')
def post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    return render_template('blog/post.html', post=post)
