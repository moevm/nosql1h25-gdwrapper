from django.urls import path
from . import views\

app_name = 'auth'

urlpatterns = [
    # path('stats/', views.stats, name='stats'),
    path('', views.auth, name='auth'),
    #callback_url
]