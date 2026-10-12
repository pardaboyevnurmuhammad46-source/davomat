import time
from .models import StudentProfile, Subject, Attendance
from celery import shared_task
from django.core.mail import send_mail
from django.utils.timezone import localdate




@shared_task(
    name='send_grade_notification_task',
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3},
)
def send_grade_notification_task(student_id, subject_id, grade_value):
    student = StudentProfile.objects.select_related('user').get(id=student_id)
    subject = Subject.objects.get(id=subject_id)

    # if student.telegram_id:
    #     requests.post(
    #         f"https://api.telegram.org/bot<TOKEN>/sendMessage",
    #         json={
    #             "chat_id": student.telegram_id,
    #             "text": f"Hurmatli {student.first_name}, siz {subject.name} fanidan {grade_value} baho oldingiz."
    #         }
    #     )

    if student.user.email:
        send_mail(
            subject="Yangi Baho",
            message=f"Hurmatli {student.user.first_name}, siz {subject.name} fanidan {grade_value} baho oldingiz.",
            from_email="noreply@maktab.uz",
            recipient_list=[student.user.email],
        )
    return f"Notification sent to student {student_id}"


@shared_task(
    name='send_attendance_notification_task',
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3},
)
def send_attendance_notification_task(student_id, date, status):
    student = StudentProfile.objects.select_related('user').get(id=student_id)
    holat = dict(Attendance.Status.choices).get(status, status)

    for parent in student.parents.select_related('user'):
        if parent.user.email:
            send_mail(
                subject="Davomat xabari",
                message=f"{student.user.first_name} {date} kuni: {holat}",
                from_email="noreply@maktab.uz",
                recipient_list=[parent.user.email],
            )
    return f"Attendance notification sent for student {student_id}"


@shared_task(name='send_daily_report_task', ignore_result=True)
def send_daily_report_task():
    today = localdate()
    absent = Attendance.objects.filter(date=today, status=Attendance.Status.ABSENT).count()
    late = Attendance.objects.filter(date=today, status=Attendance.Status.LATE).count()
    print(f"HISOBOT {today}: kelmadi={absent}, kechikdi={late}")
#
# @shared_task
# def send_grade_notification():
#
#     time.sleep(2)
#     print(f"NOTIFICATION: O'quvchi ID-{student_id} ga Subject ID-{subject_id} fandan {grade_value} baho qo'yildi!")
#     return f"Student {student_id} notified."
#
# @shared_task
# def send_attendance_notification_task(student_id, date, status):
#     time.sleep(2)
#     print(f"ATTENDANCE ALERT: O'quvchi ID-{student_id} {date} sanasida status: '{status}' bo'ldi.")
#     return f"Attendance notification sent for student {student_id}."

#
# @shared_task
# def send_grade_notification_task(student_id, subject_id, grade_value):




# @shared_task(name='send_grade_notification_task')
# def send_grade_notification_task(student_id, subject_id, grade_value):
#     try:
#         student = StudentProfile.objects.select_related('user').get(id=student_id)
#         subject = Subject.objects.get(id=subject_id)
#
#         message = f"Hurmatli {student.user.first_name}, siz {subject.name} fanidan {grade_value} baho oldingiz."
#
#         if student.user.email:
#             send_mail(
#                 subject="Yangi Baho",
#                 message=message,
#                 from_email="noreply@maktab.uz",
#                 recipient_list=[student.user.email],
#             )
#         return f"Notification sent to student {student_id}"
#     except Exception as e:
#         return f"Error: {str(e)}"







# @shared_task(name='send_attendance_notification_task')
# def send_attendance_notification_task(student_id, date, status):
#     pass