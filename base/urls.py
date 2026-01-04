from django.urls import path,include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path("about", views.aboutUs, name="about"),
    path("view_course", views.view_course, name="view_course"),
    path("message_view/<str:username>", views.Message_view, name="message_view"),
    path("contactUs", views.contactUs, name="contactUs"),
    path("termsAndConditions", views.termsAndConditions, name="termsAndConditions"),
    path('dashboard', views.dashboard_view, name='dashboard'),
    path('leaderboard', views.leaderboard_view, name='leaderboard'),
]
