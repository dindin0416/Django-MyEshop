from django.urls import path

from account.views import register_view

urlpatterns = [
     path('register/', register_view, name='register'),
]
