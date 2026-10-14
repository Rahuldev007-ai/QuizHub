from django.urls import path,include
from . import views

urlpatterns = [
    path('all_quiz',views.all_quiz_view,name='all_quiz'),
    path('my-quizzes', views.my_quizzes_view, name='my_quizzes'),
    path('attempt/<int:attempt_id>', views.quiz_attempt_detail_view, name='quiz_attempt_detail'),
    path('search/<str:category>',views.search_view,name='search'),
    path('retry/<int:quiz_id>', views.retry_quiz, name='retry_quiz'),
    path('<int:quiz_id>',views.quiz_view,name='quiz'),
]
