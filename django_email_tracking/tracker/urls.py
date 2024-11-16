from django.urls import path
from .views import home, track_open, track_click

urlpatterns = [
    path('', home, name='home'),
    path('track_open/', track_open, name='track_open'),
    path('track_click/', track_click, name='track_click'),
]
