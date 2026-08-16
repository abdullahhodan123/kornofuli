from django.urls import path
from . import views

urlpatterns = [
    path('',               views.home_view,     name='home'),
    path('manifest.json',  views.pwa_manifest,  name='pwa_manifest'),
    path('sw.js',          views.pwa_sw,        name='pwa_sw'),
    path('notice/add/',    views.notice_add,    name='notice_add'),
    path('notice/<int:pk>/edit/',   views.notice_edit,   name='notice_edit'),
    path('notice/<int:pk>/delete/', views.notice_delete, name='notice_delete'),
    path('manage/settings/',          views.manage_settings, name='manage_settings'),
    path('manage/<str:model_key>/',            views.manage_content, name='manage_content'),
    path('manage/<str:model_key>/<int:pk>/edit/',   views.manage_edit,   name='manage_edit'),
    path('manage/<str:model_key>/<int:pk>/delete/', views.manage_delete, name='manage_delete'),
]