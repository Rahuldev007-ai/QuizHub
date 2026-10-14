from django.shortcuts import render, redirect
from django.contrib.auth.models import User, auth
from django.contrib.auth.decorators import login_required
from django.http import Http404
from account.models import Profile
from .models import Quiz, Question, Choice, UserScore, UserAnswer
from .models import Category
from django.db.models import Q
from django.utils import timezone
import datetime
from datetime import timedelta
import random
from django.shortcuts import render, get_object_or_404
# from random import shuffle





# Create your views here.
@login_required(login_url='login')
def all_quiz_view(request):
    # Get user profile
    user_object = User.objects.get(username=request.user)
    user_profile = Profile.objects.get(user=user_object)

    # Get filters
    selected_category = request.GET.get("category")  # Get selected category
    selected_difficulty = request.GET.get("difficulty")  # Get selected difficulty

    # Start with all quizzes
    quizzes = Quiz.objects.all().order_by('-create_at')

    # Filter by category if selected
    if selected_category:
        quizzes = quizzes.filter(category__name=selected_category)

    # Filter by difficulty if selected
    if selected_difficulty in ["easy", "medium", "hard"]:
        quizzes = quizzes.filter(question__difficulty=selected_difficulty).distinct()

    # Get all categories
    categories = Category.objects.all()

    context = {
        "user_profile": user_profile,
        "quizzes": quizzes,
        "categories": categories,
        "selected_category": selected_category,  # Send selected category to template
        "selected_difficulty": selected_difficulty  # Send selected difficulty to template
    }

    return render(request, "all-quiz.html", context)

@login_required(login_url='login')
def search_view(request,category):

    user_object = User.objects.get(username=request.user)
    user_profile = Profile.objects.get(user=user_object)
    #sarch bt category 
    if request.GET.get('q') != None:
        q = request.GET.get('q')
        query = Q(title__icontains=q) | Q(description__icontains=q)
        quizzes = Quiz.objects.filter(query)

    #search by serchbar
    elif category != " ":
        quizzes = Quiz.objects.filter(category__name = category)
        
    else:
        quizzes = Quiz.objects.order_by('-create_at')
         
    categories  = Category.objects.all()
    return render(request,'all-quiz.html',context={"user_profile":user_profile,"quizzes":quizzes, "categories": categories})



@login_required(login_url='login')
def quiz_view(request, quiz_id):
    try:
        quiz = Quiz.objects.get(id=quiz_id)

        # Get selected difficulty from URL parameters
        selected_difficulty = request.GET.get('difficulty')

        if request.method == 'GET':
            # Get questions based on difficulty level
            if selected_difficulty in ["easy", "medium", "hard"]:
                questions = list(quiz.question_set.filter(difficulty=selected_difficulty))
            else:
                questions = list(quiz.question_set.all())  # Default: all questions

            total_questions = len(questions)

            # Ensure we pick a max of 10 random questions
            if total_questions > 10:
                questions = random.sample(questions, 10)
            else:
                random.shuffle(questions)

            # Store selected questions in session
            question_ids = [q.id for q in questions]
            request.session['quiz_questions'] = question_ids
            request.session['selected_difficulty'] = selected_difficulty  # Store difficulty in session

            first_question = questions[0] if questions else None
            return render(request, 'quiz_one_by_one.html', {
                'quiz': quiz,
                'question': first_question,
                'total_questions': len(questions),
                'questions': questions,
            })

        elif request.method == 'POST':
            # Retrieve questions from session
            question_ids = request.session.get('quiz_questions', [])
            selected_difficulty = request.session.get('selected_difficulty', None)

            # Fetch questions based on session data
            if question_ids:
                questions = list(Question.objects.filter(id__in=question_ids))
            else:
                posted_ids = [int(k.replace('question_', '')) for k in request.POST.keys() if k.startswith('question_') and k.replace('question_', '').isdigit()]
                if posted_ids:
                    questions = list(Question.objects.filter(id__in=posted_ids))
                else:
                    questions = list(quiz.question_set.all()[:10])

            correct_answers = 0
            incorrect_answers = 0
            user_answers = {}

            for question in questions:
                user_choice_id = request.POST.get(f'question_{question.id}')
                correct_choice = question.choice_set.filter(is_correct=True).first()  # Fetch the correct choice

                if user_choice_id:
                    try:
                        choice = Choice.objects.get(id=user_choice_id)
                        is_correct = choice.is_correct
                        user_answers[question.id] = {
                            'question_text': question.text,
                            'user_choice': choice,
                            'correct_choice': correct_choice,
                            'is_correct': is_correct,
                        }
                        if is_correct:
                            correct_answers += 1
                        else:
                            incorrect_answers += 1
                    except Choice.DoesNotExist:
                        user_answers[question.id] = {
                            'question_text': question.text,
                            'user_choice': None,
                            'correct_choice': correct_choice,
                            'is_correct': False,
                        }
                        incorrect_answers += 1
                else:
                    # User didn't answer this question
                    user_answers[question.id] = {
                        'question_text': question.text,
                        'user_choice': None,
                        'correct_choice': correct_choice,
                        'is_correct': False,
                    }
                    incorrect_answers += 1

            # Parse time taken
            time_taken_str = request.POST.get('time_taken')
            try:
                if time_taken_str and len(time_taken_str) <= 5:  # Format 'MM:SS'
                    time_taken = datetime.timedelta(
                        minutes=int(time_taken_str.split(':')[0]),
                        seconds=int(time_taken_str.split(':')[1])
                    )
                elif time_taken_str:  # Format 'HH:MM:SS'
                    h, m, s = map(int, time_taken_str.split(':'))
                    time_taken = datetime.timedelta(hours=h, minutes=m, seconds=s)
                else:
                    time_taken = datetime.timedelta(0)
            except (ValueError, IndexError):
                time_taken = datetime.timedelta(0)

            # Save user score to the database
            user_score = UserScore.objects.create(
                user=request.user,
                quiz=quiz,
                score=correct_answers,
                total_questions=len(questions),
                time_taken=time_taken
            )
            user_score.save()

            # Save detailed user answers for persistent historical review
            for question in questions:
                ua_data = user_answers.get(question.id, {})
                choice_obj = ua_data.get('user_choice')
                is_corr = ua_data.get('is_correct', False)
                UserAnswer.objects.create(
                    user_score=user_score,
                    question=question,
                    selected_choice=choice_obj,
                    is_correct=is_corr
                )

            # Format time for display
            formatted_time_taken = str(time_taken).split('.')[0]
            total_count = len(questions)
            accuracy = round((correct_answers / total_count) * 100) if total_count else 0

            # Build full detailed breakdown for immediate result review
            breakdown = []
            for i, question in enumerate(questions, 1):
                ua_data = user_answers.get(question.id, {})
                choice_obj = ua_data.get('user_choice')
                is_corr = ua_data.get('is_correct', False)
                correct_choice = question.choice_set.filter(is_correct=True).first()
                
                choices_list = []
                for ch in question.choice_set.all():
                    choices_list.append({
                        'id': ch.id,
                        'text': ch.text,
                        'is_correct': ch.is_correct,
                        'is_user_choice': (choice_obj and choice_obj.id == ch.id),
                    })
                
                breakdown.append({
                    'index': i,
                    'question': question,
                    'selected_choice': choice_obj,
                    'correct_choice': correct_choice,
                    'is_correct': is_corr,
                    'choices': choices_list,
                })

            # Context for result page
            context = {
                'quiz': quiz,
                'score': correct_answers,
                'total': total_count,
                'total_count': total_count,
                'incorrect': incorrect_answers,
                'incorrect_count': incorrect_answers,
                'accuracy': accuracy,
                'user_answers': user_answers,
                'breakdown': breakdown,
                'time_taken': formatted_time_taken,
                'formatted_time': formatted_time_taken,
                'attempt_id': user_score.id,
            }
            return render(request, 'quiz_result.html', context)

    except Quiz.DoesNotExist:
        messages.error(request, "The requested quiz does not exist.")
        return redirect('all_quiz')

@login_required(login_url='login')
def retry_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    request.session['quiz_questions'] = None
    request.session[f'quiz_{quiz_id}'] = None
    return redirect('quiz', quiz_id=quiz.id)

@login_required(login_url='login')
def my_quizzes_view(request):
    attempts = UserScore.objects.filter(user=request.user).select_related('quiz', 'quiz__category').order_by('-completed_at')
    
    total_attempts = attempts.count()
    if total_attempts > 0:
        total_score_sum = sum(a.score for a in attempts)
        total_questions_sum = sum(a.total_questions for a in attempts if a.total_questions > 0) or (total_attempts * 10)
        avg_accuracy = round((total_score_sum / total_questions_sum) * 100) if total_questions_sum else 0
        best_score = max((a.score for a in attempts), default=0)
    else:
        avg_accuracy = 0
        best_score = 0

    context = {
        'attempts': attempts,
        'total_attempts': total_attempts,
        'avg_accuracy': avg_accuracy,
        'best_score': best_score,
    }
    return render(request, 'my_quizzes.html', context)

@login_required(login_url='login')
def quiz_attempt_detail_view(request, attempt_id):
    if request.user.is_superuser:
        attempt = get_object_or_404(UserScore.objects.select_related('quiz', 'quiz__category', 'user'), id=attempt_id)
    else:
        attempt = get_object_or_404(UserScore.objects.select_related('quiz', 'quiz__category', 'user'), id=attempt_id, user=request.user)

    answers_qs = attempt.user_answers.select_related('question', 'selected_choice').all()
    
    breakdown = []
    if answers_qs.exists():
        for i, ans in enumerate(answers_qs, 1):
            correct_choice = ans.question.choice_set.filter(is_correct=True).first()
            choices_list = []
            for ch in ans.question.choice_set.all():
                choices_list.append({
                    'id': ch.id,
                    'text': ch.text,
                    'is_correct': ch.is_correct,
                    'is_user_choice': (ans.selected_choice_id == ch.id),
                })
            breakdown.append({
                'index': i,
                'question': ans.question,
                'selected_choice': ans.selected_choice,
                'correct_choice': correct_choice,
                'is_correct': ans.is_correct,
                'choices': choices_list,
            })
    else:
        # Graceful fallback for historical scores
        sample_questions = list(attempt.quiz.question_set.all()[:attempt.total_questions])
        for i, q in enumerate(sample_questions, 1):
            correct_choice = q.choice_set.filter(is_correct=True).first()
            is_c = (i <= attempt.score)
            selected = correct_choice if is_c else q.choice_set.filter(is_correct=False).first()
            choices_list = []
            for ch in q.choice_set.all():
                choices_list.append({
                    'id': ch.id,
                    'text': ch.text,
                    'is_correct': ch.is_correct,
                    'is_user_choice': (selected and selected.id == ch.id),
                })
            breakdown.append({
                'index': i,
                'question': q,
                'selected_choice': selected,
                'correct_choice': correct_choice,
                'is_correct': is_c,
                'choices': choices_list,
            })

    total_count = attempt.total_questions or len(breakdown) or 10
    accuracy = round((attempt.score / total_count) * 100) if total_count else 0
    formatted_time = str(attempt.time_taken).split('.')[0]

    context = {
        'attempt': attempt,
        'quiz': attempt.quiz,
        'breakdown': breakdown,
        'total_count': total_count,
        'incorrect_count': max(0, total_count - attempt.score),
        'accuracy': accuracy,
        'formatted_time': formatted_time,
    }
    return render(request, 'quiz_attempt_detail.html', context)