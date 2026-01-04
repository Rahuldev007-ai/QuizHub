from django.shortcuts import render, HttpResponse, redirect
from quiz1.models import UserScore
from django.http import HttpResponseForbidden
from django.contrib.auth.models import User
from account.models import Profile
from quiz1.models import Quiz,Question
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ContactMessage
from django.contrib import messages



# Create your views here.
def home(request):
    # Fetch leaderboard users based on rank (Assuming 'rank' exists in UserScore model)
    leaderboard_user = (
        UserScore.objects.select_related('user', 'quiz')
        .order_by('-score', 'time_taken')[:4]
    )
    
    if request.user.is_authenticated:
        # Fetch the logged-in user's profile
        user_object = User.objects.get(username=request.user)
        user_profile = Profile.objects.get(user=user_object)
        context = {
            "user_profile": user_profile,
            "leaderboard_user": leaderboard_user
        }
    else:
        # If not authenticated, just pass the leaderboard data
        context = {
            "leaderboard_user": leaderboard_user
        }

    # Render the home page with the context
    return render(request, 'welcome.html', context)

@login_required(login_url='login')
def leaderboard_view(request):
    if request.user.is_authenticated:
        # Fetch the logged-in user's profile
        user_object = User.objects.get(username=request.user)
        user_profile = Profile.objects.get(user=user_object)
    else:
        user_profile = None  # If not authenticated, no user profile

    # Fetch top users sorted by highest score
    leaderboard_user = (
        UserScore.objects.select_related('user', 'quiz')
        .order_by('-score', 'time_taken')[:12]
    )

    # Pass the leaderboard and user profile (if authenticated) to the context
    context = {
        "leaderboard_user": leaderboard_user,
        "user_profile": user_profile,
    }
    

    return render(request, 'leaderboard.html', context)

@login_required(login_url='login')
def dashboard_view(request):

    if request.user.is_superuser:

    # Fetch top users sorted by highest score and shortest time
        top_users = (
            UserScore.objects.select_related('user', 'quiz')
            .order_by('-score', 'time_taken')[:4]
        )

        quizzes = Quiz.objects.all()  # Replace with the appropriate query
        submissions = UserScore.objects.count()
        questions = Question.objects.count()  # Replace with the appropriate model
        
        user_profile = None
        if request.user.is_authenticated:
            user_object = get_object_or_404(User, username=request.user)
            user_profile = get_object_or_404(Profile, user=user_object)
            mails = ContactMessage.objects.all()

        context = {
            "top_users": top_users,
            "quizzes": quizzes,
            "submissions": submissions,
            "questions": questions,
            "user_profile": user_profile,
            'mails': mails,
        }

        return render(request, 'dashboard.html', context)
    else:
        return HttpResponseForbidden("You do not have permission to access this page.")


def aboutUs(request):
    return render(request,'about.html')

def termsAndConditions(request):
    return render(request,'terms-conditions.html')

@login_required(login_url='login')
def contactUs(request):
    user_object = get_object_or_404(User, username=request.user)
    user_profile = get_object_or_404(Profile, user=user_object)

    if request.method == "POST":
        subject = request.POST['subject']
        message = request.POST['message']

        # Create a new ContactMessage object
        ContactMessage.objects.create(
            user=request.user,
            subject=subject,
            message=message
        )

        # Success message after form submission
        messages.success(request, "Your message has been sent successfully!")

        # Render the profile page with the user and additional context
        context = {"user_profile": user_profile}
        return render(request, 'welcome.html', context)

    else:
        # Render the contact-us page if it's not a POST request
        context = {"user_profile": user_profile}
        return render(request, 'contact-us.html', context)
    
    
def Message_view(request, username):
    # Fetching the user by username
    user_object = get_object_or_404(User, username=username)  # Fetch the user by their username
    user_profile = get_object_or_404(Profile, user=user_object)  # Fetch the profile of the user

    # Fetching messages related to the user
    messages = ContactMessage.objects.filter(user=user_object)  # Filter messages for this user

    # Debugging: print number of messages to the console
    print(f"Number of messages for {username}: {messages.count()}")

    # Passing the necessary data to the template
    context = {
        'messages': messages,  # List of messages related to this user
        'user_profile': user_profile,  # The profile of the user
        'username': username  # The username of the user
    }

    return render(request, 'message.html', context)

@login_required(login_url='login')
def view_course(request):
    return render(request,'view_course.html')