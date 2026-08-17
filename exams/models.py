from django.db import models
from django.core.validators import MinValueValidator
from accounts.models import User, ClassRoom, Student


# Reusable marker for "not yet cached"
_UNSET = object()


class Exam(models.Model):
    EXAM_TYPE_CHOICES = [
        ('weekly', 'Weekly Test'),
        ('monthly', 'Monthly Test'),
        ('midterm', 'Mid Term'),
        ('final', 'Final Exam'),
    ]

    name = models.CharField(max_length=200)
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPE_CHOICES)
    classroom = models.ForeignKey(
        ClassRoom,
        on_delete=models.CASCADE,
        related_name='exams'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_exams'
    )
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['created_by', '-date']),
        ]

    def __str__(self):
        return f"{self.name} — {self.classroom.name}"


class Subject(models.Model):
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='subjects'
    )
    name = models.CharField(max_length=100)
    full_marks = models.PositiveIntegerField(default=100)
    pass_marks = models.PositiveIntegerField(default=33)
    is_optional = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.exam.name})"


class Result(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='results'
    )
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='results'
    )
    serial = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'exam')

    def __str__(self):
        return f"{self.student.full_name} — {self.exam.name}"

    # --------------------------------------------------
    # Cached mark_entries — loaded once, reused everywhere
    # --------------------------------------------------

    @property
    def entries(self):
        if not hasattr(self, '_cached_entries'):
            self._cached_entries = list(
                self.mark_entries.select_related('subject').all()
            )
        return self._cached_entries

    # -----------------------------
    # Total Marks
    # -----------------------------

    def total_marks(self):
        return sum(float(e.marks_obtained) for e in self.entries)

    def total_full_marks(self):
        return sum(e.subject.full_marks for e in self.entries)

    def percentage(self):
        full = self.total_full_marks()
        if not full:
            return 0.0
        return round((self.total_marks() / full) * 100, 2)

    # -----------------------------
    # GPA Calculation
    # -----------------------------

    @staticmethod
    def _grade_point(percentage):
        if percentage >= 80:
            return 5.0
        elif percentage >= 70:
            return 4.0
        elif percentage >= 60:
            return 3.5
        elif percentage >= 50:
            return 3.0
        elif percentage >= 40:
            return 2.0
        elif percentage >= 33:
            return 1.0
        return 0.0

    def gpa(self):
        entries = self.entries

        if not entries:
            return 0.0

        total_gp = 0.0
        subject_count = 0
        optional_bonus = 0.0

        for entry in entries:
            subject = entry.subject
            marks = float(entry.marks_obtained)
            pct = (marks / float(subject.full_marks)) * 100
            gp = self._grade_point(pct)

            if subject.is_optional:
                if gp > 2.0:
                    optional_bonus = gp - 2.0
                continue

            if marks < float(subject.pass_marks):
                return 0.0

            total_gp += gp
            subject_count += 1

        if subject_count == 0:
            return 0.0

        base_gpa = total_gp / subject_count
        final_gpa = base_gpa + (optional_bonus / subject_count)
        return round(min(final_gpa, 5.0), 2)

    # -----------------------------
    # Letter Grade
    # -----------------------------

    def letter_grade(self):
        if self.is_failed():
            return 'F'

        gpa = self.gpa()

        if gpa >= 5.0:
            return 'A+'
        elif gpa >= 4.0:
            return 'A'
        elif gpa >= 3.5:
            return 'A-'
        elif gpa >= 3.0:
            return 'B'
        elif gpa >= 2.0:
            return 'C'
        elif gpa >= 1.0:
            return 'D'
        return 'F'

    # -----------------------------
    # Pass / Fail
    # -----------------------------

    def is_failed(self):
        return any(
            float(e.marks_obtained) < float(e.subject.pass_marks)
            for e in self.entries
            if not e.subject.is_optional
        )

    # -----------------------------
    # Best / Worst Subject
    # -----------------------------

    def best_subject(self):
        entries = self.entries
        return max(entries, key=lambda e: e.marks_obtained) if entries else None

    def worst_subject(self):
        entries = self.entries
        return min(entries, key=lambda e: e.marks_obtained) if entries else None


class MarkEntry(models.Model):
    result = models.ForeignKey(
        Result,
        on_delete=models.CASCADE,
        related_name='mark_entries'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='mark_entries'
    )
    marks_obtained = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        unique_together = ('result', 'subject')
        indexes = [
            models.Index(fields=['subject', 'result']),
        ]

    def __str__(self):
        return (
            f"{self.result.student.full_name} — "
            f"{self.subject.name}: {self.marks_obtained}"
        )

    def is_passed(self):
        return (
            float(self.marks_obtained)
            >= float(self.subject.pass_marks)
        )

    def percentage(self):
        return round(
            (
                float(self.marks_obtained)
                / self.subject.full_marks
            ) * 100,
            2
        )