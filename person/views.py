from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from account.models import Profile

@login_required(login_url='login')
def person_add(request):
    # Get the current user's profile
    user_object = User.objects.get(username=request.user)
    user_profile = Profile.objects.get(user=user_object)
    
    # Fetch all other users except the current user
    all_users = User.objects.exclude(username=request.user.username)
    
    context = {
        "user_profile": user_profile,
        "all_users": all_users,
    }
    return render(request, 'person.html', context)
