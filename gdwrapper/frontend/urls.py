<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> 1e64cc3920687e492586f9fcaee0a8a1d60b4456
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('stats/', views.stats, name='stats'),
    path('auth/', views.auth, name='auth'),
<<<<<<< HEAD
]
=======
]
=======
>>>>>>> parent of 5a254b3 (web can start and 2 pagws exist but on the same port as backend)
>>>>>>> 1e64cc3920687e492586f9fcaee0a8a1d60b4456
