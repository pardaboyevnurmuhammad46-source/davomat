from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        TEACHER = 'TEACHER', 'Ustoz'
        STUDENT = 'STUDENT', "O'quvchi"
        PARENT = 'PARENT', 'Ota-ona'

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class SchoolClass(models.Model):
    name = models.CharField(max_length=10)
    academic_year = models.CharField(max_length=9)

    class Meta:
        verbose_name = "Sinf"
        verbose_name_plural = "Sinflar"

    def __str__(self):
        return self.name


class Subject(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    subjects = models.ManyToManyField(Subject, related_name='teachers')
    is_class_teacher = models.ForeignKey(
        SchoolClass, on_delete=models.SET_NULL, null=True, blank=True, related_name='head_teacher',
        help_text="Sinf rahbari bo'lgan sinfi"
    )

    def __str__(self):
        return f"Ustoz: {self.user.get_full_name() or self.user.username}"


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    # on_delete PROTECT: o'quvchisi bor sinfni tasodifan o'chirib bo'lmaydi
    school_class = models.ForeignKey(SchoolClass, on_delete=models.PROTECT, related_name='students')
    roll_number = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"O'quvchi: {self.user.get_full_name()} ({self.school_class.name})"


class ParentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='parent_profile')
    children = models.ManyToManyField(StudentProfile, related_name='parents')

    def __str__(self):
        return f"Ota-ona: {self.user.get_full_name()}"


class Attendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = 'PRESENT', 'Kelgan'
        ABSENT = 'ABSENT', 'Kelmadi'
        LATE = 'LATE', 'Kechikdi'
        EXCUSED = 'EXCUSED', 'Sababli'

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='attendances')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.SET_NULL, null=True)
    # date = models.DateField(auto_now_add=True)
    date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PRESENT)
    remark = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        unique_together = ('student', 'subject', 'date')

    def __str__(self):
        return f"{self.student.user.first_name} - {self.date} - {self.status}"


class Grade(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='grades')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.SET_NULL, null=True)
    grade = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.CharField(max_length=255, null=True, blank=True)
    # date = models.DateField(auto_now_add=True)
    date = models.DateField(default=timezone.localdate)

    def __str__(self):
        return f"{self.student.user.first_name} - {self.subject.name}: {self.grade}"


#  Dars Jadvali
class Schedule(models.Model):
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name='schedules')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.SET_NULL, null=True, related_name='schedules')
    day = models.CharField(max_length=20)
    time = models.CharField(max_length=50)
    room = models.CharField(max_length=20)

    @property
    def teacher_name(self):
        return self.teacher.user.get_full_name() if self.teacher else ""


# E'lonlar
class Announcement(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title