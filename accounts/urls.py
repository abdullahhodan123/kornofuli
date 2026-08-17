from django.urls import path
from . import views



urlpatterns = [
    path(
        'add-student/',
        views.add_student,
        name='add_student'
    ),

    path(
        'login/',
        views.user_login,
        name='login'
    ),

    path(
        'logout/',
        views.user_logout,
        name='logout'
    ),

    path('stu_list/<int:class_id>/', views.student_list, name='student_list'),
    path('class_list/',views.class_list,name = 'class_list'),
    path('class_add/', views.add_class, name='class_add'),
    path('class/student/<int:student_id>/payment/', views.mark_payment, name='mark_payment'),
    path('class/student/<int:student_id>/delete/', views.delete_student, name='delete_student'),
    path('classroom/<int:classroom_id>/attendance/',        views.take_attendance,    name='take_attendance'),
]
    