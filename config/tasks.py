import time

from celery import shared_task
from django.core.mail import send_mail
from django.utils.timezone import localdate

from .models import Announcement, Attendance, StudentProfile, Subject, User
from .telegram import send_telegram

RETRY = dict(autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})

# xabar yuborish
def notify(user, title, text):
    if user.telegram_id and send_telegram(user.telegram_id, text):
        return
    if user.email:
        send_mail(title, text, "maktabuz", [user.email])


@shared_task(name='send_grade_notification_task', **RETRY)
def send_grade_notification_task(student_id, subject_id, grade_value):
    student = StudentProfile.objects.select_related('user').get(id=student_id)
    subject = Subject.objects.get(id=subject_id)
    text = f"{student.user.first_name}: {subject.name} fanidan {grade_value} baho oldi."

    notify(student.user, "Yangi baho", text)
    for parent in student.parents.select_related('user'):
        notify(parent.user, "Yangi baho", text)


@shared_task(name='send_attendance_notification_task', **RETRY)
def send_attendance_notification_task(student_id, date, status):
    student = StudentProfile.objects.select_related('user').get(id=student_id)
    holat = dict(Attendance.Status.choices).get(status, status)
    text = f"{student.user.first_name} {date} kuni: {holat}"

    for parent in student.parents.select_related('user'):
        notify(parent.user, "Davomat xabari", text)


@shared_task(name='send_announcement_task')
def send_announcement_task(announcement_id):
    announcement = Announcement.objects.get(id=announcement_id)
    text = f"{announcement.title}\n\n{announcement.content}"
    chat_ids = User.objects.filter(telegram_id__isnull=False).values_list('telegram_id', flat=True)
    for chat_id in chat_ids:
        send_telegram(chat_id, text)
        time.sleep(0.05)


@shared_task(name='send_daily_report_task', ignore_result=True)
def send_daily_report_task():
    today = localdate()
    absent = Attendance.objects.filter(date=today, status=Attendance.Status.ABSENT).count()
    late = Attendance.objects.filter(date=today, status=Attendance.Status.LATE).count()
    text = f"Hisobot {today}: kelmadi {absent}, kechikdi {late}"

    for admin in User.objects.filter(role=User.Role.ADMIN, telegram_id__isnull=False):
        send_telegram(admin.telegram_id, text)