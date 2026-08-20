from collections import defaultdict
from exams.models import Result
from accounts.models import Attendance, Payment


def get_full_report(student, last_n=5):
    # ── Results ──────────────────────────────────────────────────
    results = list(
        Result.objects
        .filter(student=student)
        .select_related('exam', 'exam__classroom')
        .prefetch_related('mark_entries__subject')
        .order_by('-exam__date')[:last_n]
    )

    subject_data = defaultdict(lambda: {'percentages': [], 'obtained': 0.0, 'full': 0})
    for r in results:
        for e in r.mark_entries.all():
            sd = subject_data[e.subject.name]
            sd['percentages'].append(e.percentage())
            sd['obtained']   += float(e.marks_obtained)
            sd['full']       += e.subject.full_marks

    subject_analysis = sorted([
        {
            'subject': name,
            'avg':     round(sum(d['percentages']) / len(d['percentages']), 1),
            'high':    round(max(d['percentages']), 1),
            'low':     round(min(d['percentages']), 1),
            'count':   len(d['percentages']),
        }
        for name, d in subject_data.items()
    ], key=lambda x: x['avg'], reverse=True)

    overall = {}
    if results:
        pcts = [r.percentage() for r in results]
        gpas = [r.gpa() for r in results]
        overall = {
            'avg_pct':  round(sum(pcts) / len(pcts), 1),
            'avg_gpa':  round(sum(gpas) / len(gpas), 2),
            'best':     round(max(pcts), 1),
            'worst':    round(min(pcts), 1),
            'passed':   sum(1 for r in results if not r.is_failed()),
            'failed':   sum(1 for r in results if r.is_failed()),
        }

    # ── Attendance — single query ───────────────────────────────
    atts = list(
        Attendance.objects.filter(student=student)
        .order_by('-date')
    )

    total   = len(atts)
    present = sum(1 for a in atts if a.status == 'present')
    absent  = sum(1 for a in atts if a.status == 'absent')
    late    = sum(1 for a in atts if a.status == 'late')

    monthly_map = defaultdict(lambda: {'present': 0, 'absent': 0, 'late': 0, 'total': 0})
    for a in atts:
        key = (a.date.year, a.date.month)
        monthly_map[key][a.status] += 1
        monthly_map[key]['total']  += 1

    monthly_att = [
        {
            'label':   f"{y}-{m:02d}",
            'present': v['present'],
            'absent':  v['absent'],
            'late':    v['late'],
            'total':   v['total'],
            'pct':     round(v['present'] / v['total'] * 100, 1) if v['total'] else 0,
        }
        for (y, m), v in sorted(monthly_map.items(), reverse=True)
    ]

    attendance = {
        'total': total, 'present': present,
        'absent': absent, 'late': late,
        'pct': round(present / total * 100, 1) if total else 0,
        'monthly': monthly_att,
        'recent':  list(atts[:30]),
    }

    # ── Payments ─────────────────────────────────────────────────
    payments = list(
        Payment.objects
        .filter(student=student)
        .order_by('-year', '-month')
    )

    return {
        'student':          student,
        'results':          results,
        'subject_analysis': subject_analysis,
        'best_subject':     subject_analysis[0]  if subject_analysis else None,
        'worst_subject':    subject_analysis[-1] if subject_analysis else None,
        'overall':          overall,
        'attendance':       attendance,
        'payments':         payments,
        'last_n':           last_n,
        'actual_count':     len(results),
    }