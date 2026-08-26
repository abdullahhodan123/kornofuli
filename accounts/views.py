from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from datetime import datetime
from django.shortcuts import render, get_object_or_404
from .models import Student, Payment, ClassRoom, Attendance
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from datetime import date, time, datetime
from django.utils import timezone
from django.db.models import Count, Q, Subquery, BooleanField
import requests
import threading
from django.conf import settings
 
from .forms import (
    StudentAddForm,
    StudentEditForm,
    ClassRoomForm,
    UserLoginForm
)



# ─────────────────────────────────────────
#  Authorization
# ─────────────────────────────────────────

def teacher_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'teacher':
            messages.error(request, 'শুধুমাত্র Teacher প্রবেশ করতে পারবেন।')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


# ─────────────────────────────────────────
#  SMS Utilities
# ─────────────────────────────────────────
 
def format_bd_number(phone):
    number = phone.strip().replace(' ', '').replace('-', '')
    if number.startswith('0'):
        return '88' + number
    return number
 
 
def send_sms(to_number, message):
    number = format_bd_number(to_number)
    url = "http://bulksmsbd.net/api/smsapi"
    params = {
        'api_key':  settings.BULKSMS_API_KEY,
        'type':     'text',
        'number':   number,
        'senderid': settings.BULKSMS_SENDER_ID,
        'message':  message,
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        if data.get('response_code') == 202:
            print(f"✅ SMS sent to {number}")
            return True
        else:
            print(f"❌ SMS failed: {data}")
            return False
    except Exception as e:
        print(f"❌ SMS error: {e}")
        return False
 
 
def send_attendance_sms(student, status, date):
    status_text = "অনুপস্থিত" if status == 'absent' else "দেরিতে এসেছে"
    message = (
        f"প্রিয় অভিভাবক,\n\n"
        f"আপনার সন্তান {student.full_name} "
        f"আজ ({date.strftime('%d/%m/%Y')}) ক্লাসে {status_text}।\n\n"
        f"ধন্যবাদ,\n"
        f"কর্ণফুলী বিজ্ঞান একাডেমি"
    )
    if student.guardian_phone_1:
        send_sms(student.guardian_phone_1, message)
    if student.guardian_phone_2:
        send_sms(student.guardian_phone_2, message)
 
 
def send_attendance_sms_async(student, status, date):
    thread = threading.Thread(
        target=send_attendance_sms,
        args=(student, status, date)
    )
    thread.daemon = True
    thread.start()
 
 
# নতুন: Payment confirmation SMS
def send_payment_sms(student, month, year):
    month_names_bn = {
        1: "জানুয়ারি", 2: "ফেব্রুয়ারি", 3: "মার্চ", 4: "এপ্রিল",
        5: "মে", 6: "জুন", 7: "জুলাই", 8: "আগস্ট",
        9: "সেপ্টেম্বর", 10: "অক্টোবর", 11: "নভেম্বর", 12: "ডিসেম্বর"
    }
    month_name = month_names_bn.get(month, str(month))
 
    message = (
        f"প্রিয় অভিভাবক,\n\n"
        f"আপনার সন্তান {student.full_name}-এর {month_name} {year} "
        f"মাসের বেতন সফলভাবে গ্রহণ করা হয়েছে।\n\n"
        f"ধন্যবাদান্তে,\n"
        f"কর্ণফুলী বিজ্ঞান একাডেমি"
    )
 
    if student.guardian_phone_1:
        send_sms(student.guardian_phone_1, message)
    if student.guardian_phone_2:
        send_sms(student.guardian_phone_2, message)
 
 
def send_payment_sms_async(student, month, year):
    thread = threading.Thread(
        target=send_payment_sms,
        args=(student, month, year)
    )
    thread.daemon = True
    thread.start()
 
 
# ─────────────────────────────────────────
#  Auth Views
# ─────────────────────────────────────────
 
@teacher_required
def add_student(request):
    """Teacher নতুন student account বানায়। Student নিজে register করতে পারবে না।"""
    if request.method == 'POST':
        form = StudentAddForm(request.POST)
        if form.is_valid():
            user = form.save()
            student = user.student
            messages.success(request, f"{student.full_name} added successfully.")
            return redirect('student_list', class_id=student.classroom_id)
    else:
        form = StudentAddForm()

    return render(request, 'add_student.html', {'form': form})


@teacher_required
def edit_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    if request.method == 'POST':
        form = StudentEditForm(request.POST, student=student)
        if form.is_valid():
            form.save()
            messages.success(request, f"{student.full_name} updated successfully.")
            return redirect('student_list', class_id=student.classroom_id)
    else:
        form = StudentEditForm(
            student=student,
            initial={
                'full_name': student.full_name,
                'school_name': student.school_name,
                'classroom': student.classroom,
                'guardian_phone_1': student.guardian_phone_1,
                'guardian_phone_2': student.guardian_phone_2,
            }
        )

    return render(request, 'edit_student.html', {'form': form, 'student': student})


def user_login(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()

            if user.role == 'student':
                messages.error(
                    request,
                    "Student login is disabled. Only teachers can access the panel."
                )
                return redirect('login')

            login(request, user)
            messages.success(request, "Login successful.")
            return redirect('home')
    else:
        form = UserLoginForm()

    return render(request, 'login.html', {'form': form})
 
 
def user_logout(request):
    logout(request)
    messages.success(request, "Logout successful.")
    return redirect('login')
 
 
# ─────────────────────────────────────────
#  Main Views
# ─────────────────────────────────────────
 
# def home(request):
#     return render(request, 'home.html')
 
 
@teacher_required
def class_list(request):
    classes = ClassRoom.objects.annotate(student_count=Count('student'))
    return render(request, 'class_list.html', {'classes': classes})


@teacher_required
def add_class(request):
    """Teacher নতুন class বানায়।"""
    if request.method == 'POST':
        form = ClassRoomForm(request.POST)
        if form.is_valid():
            room = form.save()
            messages.success(request, f"{room.name} added successfully.")
            return redirect('class_list')
    else:
        form = ClassRoomForm()

    return render(request, 'class_add.html', {'form': form})


@teacher_required
def edit_class(request, pk):
    """Teacher class name edit করতে পারে।"""
    classroom = get_object_or_404(ClassRoom, pk=pk)
    if request.method == 'POST':
        form = ClassRoomForm(request.POST, instance=classroom)
        if form.is_valid():
            form.save()
            messages.success(request, f"{classroom.name} updated successfully.")
            return redirect('class_list')
    else:
        form = ClassRoomForm(instance=classroom)

    return render(request, 'class_edit.html', {'form': form, 'classroom': classroom})


@teacher_required
def student_list(request, class_id):
    now = datetime.now()
    current_month = now.month
    current_year  = now.year
 
    classroom = get_object_or_404(ClassRoom, id=class_id)
    students  = Student.objects.filter(
        classroom=classroom,
        is_approved=True
    ).select_related('user', 'classroom').order_by('full_name')

    query = request.GET.get('q', '').strip()
    if query:
        students = students.filter(
            Q(full_name__icontains=query) |
            Q(school_name__icontains=query) |
            Q(guardian_phone_1__icontains=query) |
            Q(guardian_phone_2__icontains=query) |
            Q(user__username__icontains=query)
        )

    paginator = Paginator(students, 10)
    page_obj  = paginator.get_page(request.GET.get('page'))

    paid_student_ids = set(
        Payment.objects.filter(
            student__in=page_obj.object_list,
            month=current_month,
            year=current_year,
            is_paid=True
        ).values_list('student_id', flat=True)
    )

    student_data = [
        {'student': s, 'is_paid': s.id in paid_student_ids}
        for s in page_obj.object_list
    ]

    total_count = paginator.count
    paid_count = Payment.objects.filter(
        student__classroom=classroom,
        month=current_month,
        year=current_year,
        is_paid=True
    ).distinct().count()

    context = {
        'classroom':    classroom,
        'student_data': student_data,
        'month':        current_month,
        'year':         current_year,
        'paid_count':   paid_count,
        'unpaid_count': total_count - paid_count,
        'total_count':  total_count,
        'page_obj':     page_obj,
        'query':        query,
    }
    return render(request, 'student_list.html', context)
 
 
@teacher_required
@require_POST
def mark_payment(request, student_id):
    now     = datetime.now()
    student = get_object_or_404(Student, id=student_id)
 
    payment, created = Payment.objects.get_or_create(
        student=student,
        month=now.month,
        year=now.year,
        defaults={'is_paid': True}
    )
 
    if not created:
        payment.is_paid = not payment.is_paid
        payment.save()
 
    # নতুন paid হলেই SMS যাবে, unpaid করলে যাবে না
    if payment.is_paid:
        send_payment_sms_async(student, now.month, now.year)
 
    return JsonResponse({'is_paid': payment.is_paid})
 

@teacher_required
@require_POST
def delete_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    name = student.full_name
    user = student.user
    student.delete()
    user.delete()
    return JsonResponse({'deleted': True, 'name': name})
 

# ─────────────────────────────────────────
#  Attendance View  (SMS যোগ করা হয়েছে)
# ─────────────────────────────────────────
 
@teacher_required
def take_attendance(request, classroom_id):
    classroom = get_object_or_404(ClassRoom, id=classroom_id)
    students  = Student.objects.filter(classroom=classroom, is_approved=True).select_related('user', 'classroom').order_by('full_name')
    today     = timezone.localdate()
 
    if request.method == 'POST':
        for student in students:
            status = request.POST.get(f'status_{student.id}', 'absent')
 
            attendance, created = Attendance.objects.update_or_create(
                student=student,
                date=today,
                defaults={'status': status}
            )
 
            # শুধু প্রথমবার attendance নেওয়ার সময় SMS যাবে, পরে edit করলে যাবে না
            if created and status in ('absent', 'late'):
                send_attendance_sms_async(student, status, today)
 
        messages.success(request, f"Attendance saved for {today.strftime('%d %B %Y')} ✓")
        return redirect('take_attendance', classroom_id=classroom.id)
 
    # আজকের existing attendance
    existing     = Attendance.objects.filter(student__classroom=classroom, date=today)
    existing_map = {a.student_id: a.status for a in existing}
 
    # Summary — single aggregate query instead of N*3
    summary_qs = (
        Attendance.objects
        .filter(student__classroom=classroom)
        .values('student_id')
        .annotate(
            present=Count('id', filter=Q(status='present')),
            absent=Count('id', filter=Q(status='absent')),
            late=Count('id', filter=Q(status='late')),
        )
    )
    summary_map = {s['student_id']: s for s in summary_qs}

    total_days = Attendance.objects.filter(
        student__classroom=classroom
    ).values('date').distinct().count()
 
    student_summary = []
    for student in students:
        s = summary_map.get(student.id, {})
        student_summary.append({
            'student': student,
            'present': s.get('present', 0),
            'absent':  s.get('absent', 0),
            'late':    s.get('late', 0),
            'today':   existing_map.get(student.id, None),
        })
 
    context = {
        'classroom':       classroom,
        'students':        students,
        'student_count':   len(student_summary),
        'today':           today,
        'existing_map':    existing_map,
        'already_taken':   existing.exists(),
        'student_summary': student_summary,
        'total_days':      total_days,
        'total_present':   sum(s['present'] for s in student_summary),
        'total_absent':    sum(s['absent']  for s in student_summary),
        'total_late':      sum(s['late']    for s in student_summary),
    }
    return render(request, 'take_attendance.html', context)