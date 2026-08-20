from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('student/<int:student_id>/report/',      views.teacher_student_report, name='teacher_student_report'),
    path('student/<int:student_id>/report/pdf/',  views.student_report_pdf,     name='student_report_pdf'),
    path('classroom/<int:classroom_id>/reports/pdf/', views.bulk_student_report_pdf, name='bulk_student_report_pdf'),
]