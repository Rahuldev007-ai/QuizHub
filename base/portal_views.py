import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Avg

from quiz1.models import Quiz, Question, Choice, Category, UserScore, UserAnswer
from account.models import Profile
from base.models import ContactMessage


def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff)


@user_passes_test(is_admin, login_url='login')
def portal_dashboard(request):
    """Master Administrative Dashboard Studio"""
    # 1. Telemetry Stats
    total_users = User.objects.count()
    total_quizzes = Quiz.objects.count()
    total_questions = Question.objects.count()
    total_submissions = UserScore.objects.count()
    total_categories = Category.objects.count()
    pending_inquiries = ContactMessage.objects.count()

    # 2. Quizzes with question counts
    quizzes = Quiz.objects.select_related('category').annotate(
        q_count=Count('question')
    ).order_by('-create_at')

    # 3. Categories with quiz counts
    categories = Category.objects.annotate(
        quiz_count=Count('quiz')
    ).order_by('name')

    # 4. Questions (latest 50, with quiz title and choices)
    questions = Question.objects.select_related('quiz').prefetch_related('choice_set').order_by('-id')[:50]

    # 5. Scholars / Users
    scholars = User.objects.annotate(
        attempts_count=Count('userscore')
    ).order_by('-date_joined')[:30]

    # 6. Submissions Telemetry
    submissions = UserScore.objects.select_related('user', 'quiz').order_by('-completed_at')[:30]

    # 7. Inquiries / Messages
    inquiries = ContactMessage.objects.select_related('user').order_by('-created_at')

    context = {
        'total_users': total_users,
        'total_quizzes': total_quizzes,
        'total_questions': total_questions,
        'total_submissions': total_submissions,
        'total_categories': total_categories,
        'pending_inquiries': pending_inquiries,
        'quizzes': quizzes,
        'categories': categories,
        'questions': questions,
        'scholars': scholars,
        'submissions': submissions,
        'inquiries': inquiries,
    }
    return render(request, 'portal/dashboard.html', context)


# ================================================================
# QUIZ CRUD
# ================================================================

@user_passes_test(is_admin, login_url='login')
def portal_quiz_create(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        category_id = request.POST.get('category')

        if not title:
            messages.error(request, "Assessment title is required.")
            return redirect('portal_dashboard')
        
        category = get_object_or_404(Category, id=category_id) if category_id else None
        if not category:
            messages.error(request, "A valid curriculum category must be assigned.")
            return redirect('portal_dashboard')

        quiz = Quiz.objects.create(
            title=title,
            description=description,
            category=category
        )
        messages.success(request, f"Curriculum '{quiz.title}' initialized successfully.")
        return redirect('portal_dashboard')

    return redirect('portal_dashboard')


@user_passes_test(is_admin, login_url='login')
def portal_quiz_edit(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        category_id = request.POST.get('category')

        if not title:
            messages.error(request, "Assessment title cannot be blank.")
            return redirect('portal_dashboard')

        category = get_object_or_404(Category, id=category_id) if category_id else quiz.category

        quiz.title = title
        quiz.description = description
        quiz.category = category
        quiz.save()

        messages.success(request, f"Curriculum '{quiz.title}' updated successfully.")
        return redirect('portal_dashboard')

    categories = Category.objects.all()
    return render(request, 'portal/quiz_edit.html', {'quiz': quiz, 'categories': categories})


@user_passes_test(is_admin, login_url='login')
def portal_quiz_delete(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if request.method == 'POST':
        title = quiz.title
        quiz.delete()
        messages.success(request, f"Curriculum '{title}' and its problem bank were permanently removed.")
        return redirect('portal_dashboard')
    return redirect('portal_dashboard')


# ================================================================
# CATEGORY CRUD
# ================================================================

@user_passes_test(is_admin, login_url='login')
def portal_category_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, "Category designation cannot be blank.")
        elif Category.objects.filter(name__iexact=name).exists():
            messages.error(request, f"Category '{name}' already exists.")
        else:
            cat = Category.objects.create(name=name)
            messages.success(request, f"Category '{cat.name}' registered successfully.")
    return redirect('portal_dashboard')


@user_passes_test(is_admin, login_url='login')
def portal_category_edit(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            category.name = name
            category.save()
            messages.success(request, f"Category updated to '{category.name}'.")
        else:
            messages.error(request, "Category designation cannot be blank.")
    return redirect('portal_dashboard')


@user_passes_test(is_admin, login_url='login')
def portal_category_delete(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        name = category.name
        category.delete()
        messages.success(request, f"Category '{name}' deleted.")
    return redirect('portal_dashboard')


# ================================================================
# QUESTION & CHOICES CRUD (ATOMIC DYNAMIC CREATION)
# ================================================================

@user_passes_test(is_admin, login_url='login')
def portal_question_create(request):
    if request.method == 'POST':
        quiz_id = request.POST.get('quiz')
        text = request.POST.get('text', '').strip()
        difficulty = request.POST.get('difficulty', Question.EASY)

        choice_a = request.POST.get('choice_a', '').strip()
        choice_b = request.POST.get('choice_b', '').strip()
        choice_c = request.POST.get('choice_c', '').strip()
        choice_d = request.POST.get('choice_d', '').strip()
        correct_key = request.POST.get('correct_choice', 'a').lower()

        # Validation
        if not quiz_id or not text:
            messages.error(request, "Quiz assignment and question statement are required.")
            return redirect('portal_dashboard')

        if not choice_a or not choice_b:
            messages.error(request, "A minimum of Choice A and Choice B must be specified.")
            return redirect('portal_dashboard')

        quiz = get_object_or_404(Quiz, id=quiz_id)

        try:
            with transaction.atomic():
                question = Question.objects.create(
                    quiz=quiz,
                    text=text,
                    difficulty=difficulty
                )

                choices_map = [
                    ('a', choice_a),
                    ('b', choice_b),
                    ('c', choice_c),
                    ('d', choice_d)
                ]

                for key, c_text in choices_map:
                    if c_text:
                        is_corr = (key == correct_key)
                        Choice.objects.create(
                            question=question,
                            text=c_text,
                            is_correct=is_corr
                        )

                messages.success(request, f"Problem successfully added to '{quiz.title}'.")
        except Exception as e:
            messages.error(request, f"Error saving problem: {str(e)}")

        return redirect('portal_dashboard')

    quizzes = Quiz.objects.all()
    return render(request, 'portal/question_form.html', {'quizzes': quizzes})


@user_passes_test(is_admin, login_url='login')
def portal_question_edit(request, question_id):
    question = get_object_or_404(Question.objects.select_related('quiz'), id=question_id)
    choices = list(question.choice_set.all())

    if request.method == 'POST':
        quiz_id = request.POST.get('quiz')
        text = request.POST.get('text', '').strip()
        difficulty = request.POST.get('difficulty', question.difficulty)

        choice_a = request.POST.get('choice_a', '').strip()
        choice_b = request.POST.get('choice_b', '').strip()
        choice_c = request.POST.get('choice_c', '').strip()
        choice_d = request.POST.get('choice_d', '').strip()
        correct_key = request.POST.get('correct_choice', 'a').lower()

        if not text:
            messages.error(request, "Question statement cannot be empty.")
            return redirect('portal_question_edit', question_id=question.id)

        try:
            with transaction.atomic():
                if quiz_id:
                    question.quiz = get_object_or_404(Quiz, id=quiz_id)
                question.text = text
                question.difficulty = difficulty
                question.save()

                # Recreate or update choices
                question.choice_set.all().delete()

                choices_map = [
                    ('a', choice_a),
                    ('b', choice_b),
                    ('c', choice_c),
                    ('d', choice_d)
                ]

                for key, c_text in choices_map:
                    if c_text:
                        Choice.objects.create(
                            question=question,
                            text=c_text,
                            is_correct=(key == correct_key)
                        )

            messages.success(request, "Problem and choices updated successfully.")
            return redirect('portal_dashboard')
        except Exception as e:
            messages.error(request, f"Failed to update problem: {str(e)}")

    quizzes = Quiz.objects.all()
    # Prepare choices for template
    c_a = choices[0].text if len(choices) > 0 else ""
    c_b = choices[1].text if len(choices) > 1 else ""
    c_c = choices[2].text if len(choices) > 2 else ""
    c_d = choices[3].text if len(choices) > 3 else ""
    correct_idx = 'a'
    for idx, c in enumerate(choices):
        if c.is_correct:
            correct_idx = ['a', 'b', 'c', 'd'][idx] if idx < 4 else 'a'
            break

    context = {
        'question': question,
        'quizzes': quizzes,
        'choice_a': c_a,
        'choice_b': c_b,
        'choice_c': c_c,
        'choice_d': c_d,
        'correct_choice': correct_idx,
    }
    return render(request, 'portal/question_edit.html', context)


@user_passes_test(is_admin, login_url='login')
def portal_question_delete(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    if request.method == 'POST':
        quiz_title = question.quiz.title
        question.delete()
        messages.success(request, f"Problem removed from '{quiz_title}'.")
    return redirect('portal_dashboard')


# ================================================================
# USER / SCHOLAR MANAGEMENT
# ================================================================

@user_passes_test(is_admin, login_url='login')
def portal_user_toggle_staff(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    if target_user == request.user:
        messages.error(request, "You cannot alter your own administrative status.")
        return redirect('portal_dashboard')

    if request.method == 'POST':
        target_user.is_staff = not target_user.is_staff
        target_user.save()
        status_str = "Staff privileges granted." if target_user.is_staff else "Staff privileges revoked."
        messages.success(request, f"@{target_user.username}: {status_str}")

    return redirect('portal_dashboard')


@user_passes_test(is_admin, login_url='login')
def portal_user_delete(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    if target_user == request.user:
        messages.error(request, "You cannot delete your own active superuser account.")
        return redirect('portal_dashboard')

    if request.method == 'POST':
        uname = target_user.username
        target_user.delete()
        messages.success(request, f"Scholar @{uname} record deleted.")

    return redirect('portal_dashboard')


# ================================================================
# SUBMISSIONS & INQUIRIES
# ================================================================

@user_passes_test(is_admin, login_url='login')
def portal_submission_delete(request, submission_id):
    sub = get_object_or_404(UserScore, id=submission_id)
    if request.method == 'POST':
        sub.delete()
        messages.success(request, "Assessment record deleted.")
    return redirect('portal_dashboard')


@user_passes_test(is_admin, login_url='login')
def portal_inquiry_delete(request, message_id):
    msg = get_object_or_404(ContactMessage, id=message_id)
    if request.method == 'POST':
        msg.delete()
        messages.success(request, "Inbound inquiry resolved and archived.")
    return redirect('portal_dashboard')


# ================================================================
# REAL-TIME TELEMETRY JSON API
# ================================================================

@user_passes_test(is_admin, login_url='login')
def portal_api_telemetry(request):
    """Provides live JSON telemetry for dynamic dashboard polling"""
    total_users = User.objects.count()
    total_quizzes = Quiz.objects.count()
    total_questions = Question.objects.count()
    total_submissions = UserScore.objects.count()
    pending_inquiries = ContactMessage.objects.count()

    latest_subs = list(
        UserScore.objects.select_related('user', 'quiz')
        .order_by('-completed_at')[:5]
        .values('id', 'user__username', 'quiz__title', 'score', 'total_questions', 'completed_at')
    )

    data = {
        'status': 'success',
        'metrics': {
            'total_users': total_users,
            'total_quizzes': total_quizzes,
            'total_questions': total_questions,
            'total_submissions': total_submissions,
            'pending_inquiries': pending_inquiries,
        },
        'recent_submissions': latest_subs
    }
    return JsonResponse(data)
