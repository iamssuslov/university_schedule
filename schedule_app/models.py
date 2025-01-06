from django.db import models
from django.contrib.auth.models import AbstractUser
import random


# Пользовательская модель пользователя
class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)


class Course(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 'teacher'})
    students = models.ManyToManyField(User, related_name="enrolled_courses", limit_choices_to={'user_type': 'student'})

    def __str__(self):
        return self.name


class Schedule(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    room = models.CharField(max_length=50)
    attendance_code = models.CharField(max_length=6, blank=True, null=True)

    def generate_attendance_code(self):
        self.attendance_code = str(random.randint(100000, 999999))
        self.save()
    
    def __str__(self):
        return f"{self.course.name} - {self.date} {self.time}"


class Attendance(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 'student'})
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    is_present = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(null=True, blank=True)