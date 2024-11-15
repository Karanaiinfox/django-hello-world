from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('user_login/', views.login, name='login'),
    path('callback1/', views.callback, name='callback'),
    # path('get_workspace/', views.get_workspace, name='get_workspace'),
    # path('get_projects/', views.get_projects, name='get_projects'),
    # path('get_sections/', views.get_sections, name='get_sections'),
    # path('fetch_task_id/', views.fetch_task_id, name='fetch_task_id'),
    # path('asana_dashboard/', views.asana_dashboard, name='asana_dashboard'),
    # path('sync_asana/', views.sync_asana, name='sync_asana'),
]
