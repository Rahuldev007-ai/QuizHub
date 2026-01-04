
from django.urls import path,include
from . import views


urlpatterns = [
   
    path('register/', views.register, name='register'),
    path('profile/<str:username>', views.profile, name='profile'),
    path('editProfile', views.editProfile, name='editProfile'),
    path('deleteProfile', views.deleteProfile, name='deleteProfile'),
    path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'),

]