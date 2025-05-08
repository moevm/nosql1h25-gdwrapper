from django.contrib import admin
from django.urls import path, include

from . import views

urlpatterns = [
    path('refresh/', views.refresh_data, name='refresh_data'),
    path('comment/', views.create_or_update_comment, name='create_or_update_comment'),
    path('files/', views.get_all_files, name='get_all_files'),
    # path('admin/', admin.site.urls),
    path('auth/', include('auth_google.urls')),
    path('stats/', views.stats, name='stats'),
    path('', views.index, name='index')
]
