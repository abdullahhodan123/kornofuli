from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Avg, Max, Min, Count
from collections import Counter
from django.http import HttpResponse
import threading
from .models import Exam, Subject, Result, MarkEntry
from .utils import update_exam_serials
from .pdf_utils import build_exam_result_pdf
from accounts.models import Student, ClassRoom
from accounts.views import send_sms, teacher_required


# ─────────────────────────────────────────
#  SMS Utility
# ─────────────────────────────────────────

def send_result_sms(exam, students):
    """Background এ সব guardian কে result SMS পাঠাও"""
    def _send():
        for student in students:
            try:
                result = Result.objects.prefetch_related(
                    'mark_entries__subject'
                ).get(student=student, exam=exam)

                entries = result.mark_entries.select_related('subject').all()
                if not entries:
                    continue

                # Subject wise marks + grade
                subject_lines = []
                for entry in entries:
                    marks = float(entry.marks_obtained)
                    full  = float(entry.subject.full_marks)
                    pct   = (marks / full) * 100
                    # Grade letter
                    if pct >= 80:   grade = 'A+'
                    elif pct >= 70: grade = 'A'
                    elif pct >= 60: grade = 'A-'
                    elif pct >= 50: grade = 'B'
                    elif pct >= 40: grade = 'C'
                    elif pct >= 33: grade = 'D'
                    else:           grade = 'F'

                    optional_tag = ' (ঐচ্ছিক)' if entry.subject.is_optional else ''
                    subject_lines.append(
                        f"{entry.subject.name}{optional_tag}: {int(marks)}/{int(full)} [{grade}]"
                    )

                # Model methods থেকে সরাসরি নিন
                total    = int(result.total_marks())
                full     = int(result.total_full_marks())
                gpa      = result.gpa()
                grade    = result.letter_grade()
                status   = "অনুত্তীর্ণ" if result.is_failed() else "উত্তীর্ণ"

                subject_text = "\n".join(subject_lines)

                message = (

f"প্রিয় অভিভাবক,\n"
f"আপনার সন্তানের পরীক্ষার ফলাফল প্রকাশিত হয়েছে।\n\n"
f"পরীক্ষা: {exam.name}\n"
f"শিক্ষার্থী: {student.full_name}\n"

f"------------------\n"
f"{subject_text}\n"
f"------------------\n"
f"মোট নম্বর: {total}/{full}\n"
f"GPA: {gpa} | গ্রেড: {grade}\n"
f"ফলাফল: {status}\n\n"
f"ধন্যবাদান্তে,\n"
f"কর্ণফুলী বিজ্ঞান একাডেমি"
)


                if student.guardian_phone_1:
                    send_sms(student.guardian_phone_1, message)
                if student.guardian_phone_2:
                    send_sms(student.guardian_phone_2, message)

            except Result.DoesNotExist:
                pass

    thread = threading.Thread(target=_send)
    thread.daemon = True
    thread.start()


# ─────────────────────────────────────────
#  Views
# ─────────────────────────────────────────

@teacher_required
def exam_list(request):
    exams   = Exam.objects.filter(created_by=request.user).select_related('classroom').prefetch_related('subjects', 'results')
    paginator = Paginator(exams, 6)
    page_obj  = paginator.get_page(request.GET.get('page'))
    return render(request, 'exam_list.html', {'exams': page_obj.object_list, 'page_obj': page_obj})


@teacher_required
def exam_create(request):
    if request.method == 'POST':
        name         = request.POST.get('name', '').strip()
        exam_type    = request.POST.get('exam_type', '')
        classroom_id = request.POST.get('classroom')
        date         = request.POST.get('date')

        subject_names    = request.POST.getlist('subject_name[]')
        full_marks_list  = request.POST.getlist('full_marks[]')
        pass_marks_list  = request.POST.getlist('pass_marks[]')
        is_optional_list = request.POST.getlist('is_optional[]')

        if name and exam_type and classroom_id and date:
            classroom = get_object_or_404(ClassRoom, pk=classroom_id)
            exam = Exam.objects.create(
                name=name, exam_type=exam_type,
                classroom=classroom, created_by=request.user, date=date
            )
            for i, (s_name, full, passed) in enumerate(zip(subject_names, full_marks_list, pass_marks_list)):
                if s_name.strip():
                    Subject.objects.create(
                        exam=exam,
                        name=s_name.strip(),
                        full_marks=int(full),
                        pass_marks=int(passed),
                        is_optional=str(i) in is_optional_list
                    )
            messages.success(request, f'"{exam.name}" তৈরি হয়েছে।')
            return redirect('exams:exam_detail', pk=exam.pk)

    classrooms = ClassRoom.objects.all()
    return render(request, 'exam_create.html', {'classrooms': classrooms})


@teacher_required
def exam_detail(request, pk):
    exam     = get_object_or_404(Exam, pk=pk, created_by=request.user)
    subjects = exam.subjects.all()
    results  = exam.results.prefetch_related('mark_entries__subject').select_related('student', 'student__classroom').order_by('serial')
    return render(request, 'exam_detail.html', {
        'exam': exam, 'subjects': subjects, 'results': results
    })


@teacher_required
def exam_delete(request, pk):
    exam = get_object_or_404(Exam, pk=pk, created_by=request.user)
    if request.method == 'POST':
        exam.delete()
        messages.success(request, 'Exam মুছে ফেলা হয়েছে।')
        return redirect('exams:exam_list')
    return render(request, 'exam_confirm_delete.html', {'exam': exam})


@teacher_required
def subject_add(request, exam_pk):
    exam = get_object_or_404(Exam, pk=exam_pk, created_by=request.user)
    if request.method == 'POST':
        name        = request.POST.get('name', '').strip()
        full_marks  = request.POST.get('full_marks', 100)
        pass_marks  = request.POST.get('pass_marks', 33)
        is_optional = request.POST.get('is_optional') == 'on'
        if name:
            Subject.objects.create(
                exam=exam, name=name,
                full_marks=full_marks, pass_marks=pass_marks,
                is_optional=is_optional
            )
            messages.success(request, f'"{name}" যোগ করা হয়েছে।')
        return redirect('exams:exam_detail', pk=exam.pk)
    return render(request, 'subject_add.html', {'exam': exam})


@teacher_required
def subject_delete(request, pk):
    subject = get_object_or_404(Subject, pk=pk, exam__created_by=request.user)
    exam_pk = subject.exam.pk
    subject.delete()
    messages.success(request, 'Subject মুছে ফেলা হয়েছে।')
    return redirect('exams:exam_detail', pk=exam_pk)


@teacher_required
def mark_entry(request, exam_pk):
    exam     = get_object_or_404(Exam, pk=exam_pk, created_by=request.user)
    subjects = list(exam.subjects.all())
    students = Student.objects.filter(classroom=exam.classroom, is_approved=True).select_related('user', 'classroom')

    if request.method == 'POST':
        with transaction.atomic():
            for student in students:
                result, _ = Result.objects.get_or_create(student=student, exam=exam)
                for subject in subjects:
                    key   = f"marks_{student.pk}_{subject.pk}"
                    value = request.POST.get(key, '').strip()
                    if value:
                        MarkEntry.objects.update_or_create(
                            result=result, subject=subject,
                            defaults={'marks_obtained': float(value)}
                        )
            update_exam_serials(exam)

        # ✅ marks save হওয়ার পরে SMS পাঠাও
        send_result_sms(exam, students)

        messages.success(request, 'নম্বর সেভ হয়েছে।')
        return redirect('exams:exam_result_summary', exam_pk=exam.pk)

    existing_results = Result.objects.filter(exam=exam).prefetch_related('mark_entries')
    return render(request, 'mark_entry.html', {
        'exam': exam,
        'subjects': subjects,
        'students': students,
        'existing_results': existing_results,
    })


@teacher_required
def exam_result_summary(request, exam_pk):
    exam     = get_object_or_404(Exam, pk=exam_pk, created_by=request.user)
    subjects = list(exam.subjects.all())

    # Recalculate serials before showing summary
    update_exam_serials(exam)

    results  = (
        Result.objects.filter(exam=exam)
        .prefetch_related('mark_entries__subject')
        .select_related('student')
        .order_by('serial')
    )

    pass_count = 0
    fail_count = 0
    grade_counts = Counter()
    for r in results:
        grade = r.letter_grade()
        grade_counts[grade] += 1
        if r.is_failed():
            fail_count += 1
        else:
            pass_count += 1

    # Ordered grade breakdown
    GRADE_ORDER = ['A+', 'A', 'A-', 'B', 'C', 'D', 'F']
    grade_breakdown = [(g, grade_counts.get(g, 0)) for g in GRADE_ORDER if grade_counts.get(g, 0) > 0]

    agg = (
        MarkEntry.objects
        .filter(subject__exam=exam)
        .values('subject_id')
        .annotate(
            avg_marks=Avg('marks_obtained'),
            best_marks=Max('marks_obtained'),
            worst_marks=Min('marks_obtained'),
            entry_count=Count('id'),
        )
    )
    agg_map = {a['subject_id']: a for a in agg}

    subject_summary = []
    for subject in subjects:
        a = agg_map.get(subject.id)
        if a and a['entry_count'] > 0:
            best = MarkEntry.objects.filter(
                subject=subject, marks_obtained=a['best_marks']
            ).select_related('result__student').first()
            worst = MarkEntry.objects.filter(
                subject=subject, marks_obtained=a['worst_marks']
            ).select_related('result__student').first()
            avg = round(float(a['avg_marks']), 2)
        else:
            best = worst = avg = None
        subject_summary.append({'subject': subject, 'best': best, 'worst': worst, 'avg': avg})

    return render(request, 'result_summary.html', {
        'exam': exam, 'subjects': subjects,
        'results': results, 'subject_summary': subject_summary,
        'pass_count': pass_count, 'fail_count': fail_count,
        'grade_breakdown': grade_breakdown,
    })


@teacher_required
def exam_result_pdf(request, exam_pk):
    exam     = get_object_or_404(Exam, pk=exam_pk, created_by=request.user)
    subjects = list(exam.subjects.all())
    results  = (
        Result.objects.filter(exam=exam)
        .prefetch_related('mark_entries__subject', 'student')
        .order_by('serial')
    )

    buf = build_exam_result_pdf(exam, results, subjects)

    filename = f"{exam.name}_result_sheet.pdf".replace(' ', '_')
    response = HttpResponse(buf.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response