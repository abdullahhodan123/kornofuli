from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    Role_Choices = (
        ('teacher','Teacher'),
        ('student','Student')
    )
    role = models.CharField(max_length=20, choices=Role_Choices)



class ClassRoom(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name
    

class Student(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    full_name = models.CharField(max_length=200)

    school_name = models.CharField(max_length=200)

    classroom = models.ForeignKey(
        ClassRoom,
        on_delete=models.CASCADE
    )

    guardian_phone_1 = models.CharField(max_length=20)

    guardian_phone_2 = models.CharField(
        max_length=20,
        blank=True
    )
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.full_name


MONTH_CHOICES = [
    (1, 'January'),
    (2, 'February'),
    (3, 'March'),
    (4, 'April'),
    (5, 'May'),
    (6, 'June'),
    (7, 'July'),
    (8, 'August'),
    (9, 'September'),
    (10, 'October'),
    (11, 'November'),
    (12, 'December'),
]

class Payment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    month = models.IntegerField(choices=MONTH_CHOICES)
    year = models.IntegerField()
    is_paid = models.BooleanField(default=False)

    class Meta:
        unique_together = ('student', 'month', 'year')
        indexes = [
            models.Index(fields=['student', 'month', 'year', 'is_paid']),
        ]




class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent',  'Absent'),
        ('late',    'Late'),
    ]
    student   = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances')
    date      = models.DateField()
    time      = models.TimeField(auto_now_add=True)
    status    = models.CharField(max_length=10, choices=STATUS_CHOICES, default='absent')

    class Meta:
        unique_together = ('student', 'date')
        indexes = [
            models.Index(fields=['student', 'date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.student.full_name} — {self.date} — {self.status}"
    

