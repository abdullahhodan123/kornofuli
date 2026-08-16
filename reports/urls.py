from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('student/<int:student_id>/report/',    views.teacher_student_report, name='teacher_student_report'),
]