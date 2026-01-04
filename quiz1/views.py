from django.shortcuts import render, redirect
from django.contrib.auth.models import User, auth
from django.contrib.auth.decorators import login_required
from django.http import Http404
from account.models import Profile
from .models import Quiz, Question, Choice, UserScore
from .models import Category
from django.db.models import Q
from django.utils import timezone
import datetime,timedelta
import random
from django.shortcuts import render, get_object_or_404
# from datetime import datetime, timedelta
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
            questions = Question.objects.filter(id__in=question_ids)

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
                time_taken=time_taken
            )
            user_score.save()

            # Format time for display
            formatted_time_taken = str(time_taken).split('.')[0]

            # Context for result page
            context = {
                'quiz': quiz,
                'score': correct_answers,
                'total': len(questions),
                'incorrect': incorrect_answers,
                'user_answers': user_answers,
                'time_taken': formatted_time_taken
            }
            return render(request, 'quiz_result.html', context)

    except Quiz.DoesNotExist:
        messages.error(request, "The requested quiz does not exist.")
        return redirect('all_quiz')
# e retry_quiz view
@login_required(login_url='login')
def retry_quiz(request, quiz_id):
    # Fetch the quiz object by its ID
    quiz = get_object_or_404(Quiz, id=quiz_id)

    # Logic for resetting quiz state for the user
    # You can clear the session data, answers, or reset progress here based on your app's logic.
    request.session[f'quiz_{quiz_id}'] = None  # Example of resetting quiz data

    # Redirect to the quiz start page (you can adjust based on your requirements)
    return redirect('quiz_view', quiz_id=quiz.id)