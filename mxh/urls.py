from django.urls import path
from .views import *
urlpatterns = [
    path('login/', login_view, name='login'),
    path('home/', home, name='home'),
]