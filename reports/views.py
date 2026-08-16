from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.views.decorators.cache import never_cache

from accounts.models import Student
from .utils import get_full_report


def _parse_last_n(request):
    try:
        n = int(request.GET.get('last', 5))
        return max(1, min(n, 50))
    except (ValueError, TypeError):
        return 5


@never_cache
@login_required
def teacher_student_report(request, student_id):
    if request.user.role != 'teacher':
        raise PermissionDenied
    student = get_object_or_404(
        Student.objects.select_related('classroom', 'user'),
        id=student_id,
        is_approved=True,
    )
    last_n  = _parse_last_n(request)
    context = get_full_report(student, last_n)
    context['is_own'] = False
    return render(request, 'student_dashboard.html', context)