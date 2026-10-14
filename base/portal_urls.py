from django.urls import path
from . import portal_views

urlpatterns = [
    # Dashboard Studio
    path('', portal_views.portal_dashboard, name='portal_dashboard'),
    
    # Real-Time Telemetry API
    path('api/telemetry/', portal_views.portal_api_telemetry, name='portal_api_telemetry'),

    # Quiz Management
    path('quizzes/create/', portal_views.portal_quiz_create, name='portal_quiz_create'),
    path('quizzes/<int:quiz_id>/edit/', portal_views.portal_quiz_edit, name='portal_quiz_edit'),
    path('quizzes/<int:quiz_id>/delete/', portal_views.portal_quiz_delete, name='portal_quiz_delete'),

    # Category Management
    path('categories/create/', portal_views.portal_category_create, name='portal_category_create'),
    path('categories/<int:category_id>/edit/', portal_views.portal_category_edit, name='portal_category_edit'),
    path('categories/<int:category_id>/delete/', portal_views.portal_category_delete, name='portal_category_delete'),

    # Question & Choices Bank
    path('questions/create/', portal_views.portal_question_create, name='portal_question_create'),
    path('questions/<int:question_id>/edit/', portal_views.portal_question_edit, name='portal_question_edit'),
    path('questions/<int:question_id>/delete/', portal_views.portal_question_delete, name='portal_question_delete'),

    # Scholars & Permissions
    path('users/<int:user_id>/toggle-staff/', portal_views.portal_user_toggle_staff, name='portal_user_toggle_staff'),
    path('users/<int:user_id>/delete/', portal_views.portal_user_delete, name='portal_user_delete'),

    # Submissions & Inquiries
    path('submissions/<int:submission_id>/delete/', portal_views.portal_submission_delete, name='portal_submission_delete'),
    path('inquiries/<int:message_id>/delete/', portal_views.portal_inquiry_delete, name='portal_inquiry_delete'),
]
