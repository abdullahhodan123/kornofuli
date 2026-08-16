from django.urls import path
from . import views

app_name = 'exams'

urlpatterns = [
    path('list/',                         views.exam_list,           name='exam_list'),
    path('create/',                       views.exam_create,         name='exam_create'),
    path('<int:pk>/',                     views.exam_detail,         name='exam_detail'),
    path('<int:pk>/delete/',              views.exam_delete,         name='exam_delete'),
    path('<int:exam_pk>/subject/add/',    views.subject_add,         name='exam_subject_add'),
    path('subject/<int:pk>/delete/',      views.subject_delete,      name='exam_subject_delete'),
    path('<int:exam_pk>/marks/',          views.mark_entry,          name='exam_mark_entry'),
    path('<int:exam_pk>/result/',         views.exam_result_summary, name='exam_result_summary'),
    path('<int:exam_pk>/result/pdf/',     views.exam_result_pdf,     name='exam_result_pdf'),
]