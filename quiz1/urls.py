from django.urls import path,include
from . import views

urlpatterns = [
    path('all_quiz',views.all_quiz_view,name='all_quiz'),
    path('search/<str:category>',views.search_view,name='search'),
    path('<int:quiz_id>',views.quiz_view,name='quiz'),
    path('<int:quiz_id>', views.retry_quiz, name='retry_quiz'),
    # path('quiz/retry/<int:quiz_id>/', views.retry_quiz, name='retry_quiz'),
]
