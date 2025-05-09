from django.contrib import admin
from django.urls import path, include

from . import views

urlpatterns = [
    path('refresh/', views.refresh_data, name='refresh_data'),
    path('files/', views.get_all_files, name='get_all_files'),
    path('comment/', views.create_or_update_comment, name='create_or_update_comment'),
    # path('admin/', admin.site.urls),
    path('auth/', include('auth.urls')),
    path('stats/', views.stats, name='stats'),
    path('stats/data/', views.get_stats_data, name='get_stats_data'),
    path('', views.index, name='index'),
    path('import_data/', views.import_data, name='import_data'),
    path('export_data/', views.export_data, name='export_data'),
]
