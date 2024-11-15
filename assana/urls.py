from django.contrib import admin
from django.urls import path,include
from . import views
   
urlpatterns = [
    path('', views.asana_auth, name='asana_auth'),
    # path('login/', views.login, name='login'),
    # path('callback/', views.callback, name='callback'),
    path('get_workspace/', views.get_workspace, name='get_workspace'),
    path('get_projects/', views.get_projects, name='get_projects'),
    path('get_sections/', views.get_sections, name='get_sections'),
    # path('fetch_task_id/', views.fetch_task_id, name='fetch_task_id'),
    path('asana_auth/', views.asana_auth, name='asana_auth'),
    path('sync_asana/', views.sync_asana, name='sync_asana'),
    path('asanasync/', views.asanasync, name='sync_asana'),
    
]

    
