from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Lesson, Question, TestResult, Progress, Notification, UserBadge, Badge
from datetime import datetime

tests_bp = Blueprint('tests', __name__)

@tests_bp.route('/test/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
def quiz(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    questions = Question.query.filter_by(lesson_id=lesson_id).all()

    if not questions:
        flash('Для этого урока пока нет теста', 'info')
        return redirect(url_for('lessons.lesson', lesson_id=lesson_id))

    if request.method == 'POST':
        score = 0
        results = []
        for q in questions:
            user_answer = request.form.get(f'q_{q.id}', '')
            is_correct = user_answer == q.correct_answer
            if is_correct:
                score += 1
            results.append({
                'question': q.question_text,
                'user_answer': user_answer,
                'correct_answer': q.correct_answer,
                'is_correct': is_correct,
                'explanation': q.explanation,
                'options': {
                    'a': q.option_a, 'b': q.option_b,
                    'c': q.option_c, 'd': q.option_d
                }
            })

        total = len(questions)
        percentage = int((score / total) * 100) if total > 0 else 0
        passed = percentage >= 60

        test_result = TestResult(
            user_id=current_user.id,
            lesson_id=lesson_id,
            score=score,
            total=total,
            passed=passed
        )
        db.session.add(test_result)

        # Отметить урок как завершённый если прошёл тест
        if passed:
            prog = Progress.query.filter_by(user_id=current_user.id, lesson_id=lesson_id).first()
            if not prog:
                prog = Progress(user_id=current_user.id, lesson_id=lesson_id)
                db.session.add(prog)
            if not prog.completed:
                prog.completed = True
                prog.xp_earned = 20
                prog.completed_at = datetime.utcnow()

            # Бейдж за 100%
            if percentage == 100:
                badge = Badge.query.filter_by(condition_type='test_score', condition_value=100).first()
                if badge:
                    existing = UserBadge.query.filter_by(user_id=current_user.id, badge_id=badge.id).first()
                    if not existing:
                        db.session.add(UserBadge(user_id=current_user.id, badge_id=badge.id))

            notif = Notification(
                user_id=current_user.id,
                text=f'✅ Тест по уроку "{lesson.title}" пройден! Результат: {score}/{total}'
            )
            db.session.add(notif)

        db.session.commit()

        return render_template('tests/result.html',
            lesson=lesson,
            score=score,
            total=total,
            percentage=percentage,
            passed=passed,
            results=results
        )

    return render_template('tests/quiz.html', lesson=lesson, questions=questions)
