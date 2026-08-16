from django.db import models
from django.core.validators import MinValueValidator
from accounts.models import User, ClassRoom, Student


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

    # -----------------------------
    # Total Marks
    # -----------------------------

    def total_marks(self):
        return sum(
            float(entry.marks_obtained)
            for entry in self.mark_entries.select_related('subject').all()
        )

    def total_full_marks(self):
        return sum(
            entry.subject.full_marks
            for entry in self.mark_entries.select_related('subject').all()
        )

    def percentage(self):
        full_marks = self.total_full_marks()

        if not full_marks:
            return 0.0

        return round(
            (self.total_marks() / full_marks) * 100,
            2
        )

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
        entries = self.mark_entries.select_related('subject').all()

        if not entries:
            return 0.0

        total_gp = 0.0
        subject_count = 0
        optional_bonus = 0.0

        for entry in entries:
            subject = entry.subject
            marks = float(entry.marks_obtained)

            percentage = (
                marks / float(subject.full_marks)
            ) * 100

            gp = self._grade_point(percentage)

            # Optional / 4th Subject
            if subject.is_optional:
                if gp > 2.0:
                    optional_bonus = gp - 2.0
                continue

            # Fail in compulsory subject
            if marks < float(subject.pass_marks):
                return 0.0

            total_gp += gp
            subject_count += 1

        if subject_count == 0:
            return 0.0

        base_gpa = total_gp / subject_count

        # Bangladesh Board Rule:
        # (Optional GPA - 2) / Number of compulsory subjects
        final_gpa = base_gpa + (
            optional_bonus / subject_count
        )

        return round(
            min(final_gpa, 5.0),
            2
        )

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
            float(entry.marks_obtained) < float(entry.subject.pass_marks)
            for entry in self.mark_entries.select_related('subject').all()
            if not entry.subject.is_optional
        )

    # -----------------------------
    # Best Subject
    # -----------------------------

    def best_subject(self):
        entries = list(
            self.mark_entries.select_related('subject').all()
        )

        return max(
            entries,
            key=lambda e: e.marks_obtained
        ) if entries else None

    # -----------------------------
    # Worst Subject
    # -----------------------------

    def worst_subject(self):
        entries = list(
            self.mark_entries.select_related('subject').all()
        )

        return min(
            entries,
            key=lambda e: e.marks_obtained
        ) if entries else None


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