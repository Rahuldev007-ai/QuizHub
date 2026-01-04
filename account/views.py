from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User, auth
from django.contrib.auth.decorators import login_required
from django.http import Http404
from .models import Profile

# Register
def register(request):
    if request.user.is_authenticated:
        return redirect('profile', request.user.username)

    if request.method == "POST":
        email = request.POST.get('email')
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        username = request.POST.get('username')
        gender = request.POST.get('gender')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        context = {
            'email': email,
            'firstname': firstname,
            'lastname': lastname,
            'username': username,
            'gender': gender,
        }

        if password != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, 'register.html', context)

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already in use.")
            return render(request, 'register.html', context)

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return render(request, 'register.html', context)

        # Create user
        user = User.objects.create_user(username=username, email=email, password=password, first_name=firstname, last_name=lastname)
        user.save()

        # Log in user
        user_login = auth.authenticate(username=username, password=password)
        if user_login:
            auth.login(request, user_login)

            # Create profile and store gender
            Profile.objects.create(user=user, gender=gender)

            messages.success(request, "Registration successful.")
            return redirect('profile', username=user.username)

    return render(request, 'register.html')
# Profile
@login_required(login_url='login')
def profile(request, username):
    try:
        user_object = User.objects.get(username=username)
        user_profile = Profile.objects.get(user=user_object)
    except (User.DoesNotExist, Profile.DoesNotExist):
        raise Http404("User or Profile not found.")

    context = {'user_profile': user_profile}
    return render(request, 'profile.html', context)

# Edit Profile
def editProfile(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)

    if request.method == "POST":
        # Handle Profile Image Upload
        if request.FILES.get('image'):
            user_profile.profile_img = request.FILES['image']

        # Handle Profile Image Removal
        elif request.POST.get('remove_image') == '1':  
            user_profile.profile_img = "user.png"  # Assign default image path

        # Update Location and Bio
        user_profile.location = request.POST.get('location', user_profile.location)
        user_profile.bio = request.POST.get('bio', user_profile.bio)

        user_profile.save()
        messages.success(request, "Profile updated successfully.")
        return redirect('profile', user_object.username)

    context = {"user_profile": user_profile}
    return render(request, 'profile-edit.html', context)

# Delete Profile
def deleteProfile(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)

    if request.method == "POST":
        user_object.delete()
        user_profile.delete()
        messages.info(request, "Profile deleted successfully.")
        return redirect('login')

    context = {"user_profile": user_profile}
    return render(request, 'confirm.html', context)

# Login
from django.shortcuts import render, redirect
from django.contrib import messages, auth

from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages, auth

def login(request):
    if request.user.is_authenticated:
        return redirect('profile', request.user.username)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                auth.login(request, user)
                messages.success(request, "Logged in successfully.")
                return redirect('profile', user.username)
            else:
                messages.error(request, "Invalid password.")
                return render(request, 'login.html', {'username': username})
        except User.DoesNotExist:
            messages.error(request, "Invalid username or password.")
            return redirect('login')

    return render(request, 'login.html')

# Logout
@login_required(login_url='login')
def logout(request):
    auth.logout(request)
    return redirect('login')
