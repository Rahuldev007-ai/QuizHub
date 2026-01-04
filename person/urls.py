from django.urls import path,include
from . import views

urlpatterns = [
    path('person_add',views.person_add,name='person_add'),
]
