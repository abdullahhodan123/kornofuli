from .models import Result


def update_exam_serials(exam):
    results = list(
        exam.results.prefetch_related('mark_entries__subject').all()
    )
    results.sort(key=lambda r: r.total_marks(), reverse=True)
    for rank, result in enumerate(results, start=1):
        result.serial = rank
    Result.objects.bulk_update(results, ['serial'], batch_size=100)