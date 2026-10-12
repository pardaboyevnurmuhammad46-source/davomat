from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from django.db import transaction
from django.db.models import Avg
from django.shortcuts import get_object_or_404

from .models import (
    User, StudentProfile, TeacherProfile, ParentProfile,
    Subject, SchoolClass, Grade, Attendance,
    Announcement, Schedule
)
from .serializers import (
    StudentProfileSerializer, TeacherProfileSerializer, ParentProfileSerializer,
    SubjectSerializer, SchoolClassSerializer, GradeSerializer,
    AnnouncementSerializer, ScheduleSerializer,
    TeacherProfileCreateSerializer, StudentProfileCreateSerializer,
    ParentProfileCreateSerializer, SingleAttendanceSerializer,
    TeacherDashboardSerializer, BulkGradeCreateSerializer,
    UserCreateSerializer, AdminDashboardSerializer, StudentAnalyticsSerializer
)
from .permissions import IsAdmin, IsTeacher, IsStaff, IsAdminOrReadOnly
from .tasks import send_grade_notification_task, send_attendance_notification_task


# class SingleAttendanceAPIView(APIView):
#     def get(self, request, *args, **kwargs):
#         return Response({"detail": "Ishlayapti"})

# class StudentDashboardAPIView(APIView):
#
#     permission_classes = [IsAuthenticated]
#
#     def get(self, request):
#         # user = request.user
#         # student_profile = user.student_profile
#         student_profile = get_object_or_404(StudentProfile.objects.select_related('school_class', 'user'),
#             user = request.user
#         )
#         serializer = FullStudentDashboardSerializer(student_profile)
#         return Response(serializer.data)


class UserCreateAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    # permission_classes = [IsAdmin]


class TeacherDashboardAPIView(APIView):
    # permission_classes = [IsTeacher]

    def get(self, request):

        teacher_profile = get_object_or_404(TeacherProfile.objects.select_related('user', 'is_class_teacher').prefetch_related('subjects'))

        # serializer = TeacherProfileSerializer(teacher_profile)
        serializer = TeacherDashboardSerializer(teacher_profile)
        return Response(serializer.data)


class AdminDashboardAPIView(APIView):
    # permission_classes = [IsAdmin]

    def get(self, request):

        # techer_profile = get_object_or_404(
        #     TeacherProfile.objects.select_related('user', 'is_class_teacher').prefetch_related('subjects'),
        #     user = request.user
        # )

        total_students = StudentProfile.objects.count()
        total_teachers = TeacherProfile.objects.count()
        total_classes = SchoolClass.objects.count()
        # total_subjects = Subject.objects.count()
        # avg_result = Grade.objects.aggregate(Avg('grade'))['grade__avg']
        avg_dict = Grade.objects.aggregate(avg=Avg('grade'))
        raw_avg = avg_dict['avg']
        # school_average_grade = round(avg_result['grade__avg'], 2) if avg_result is not None else 0.0
        school_average_grade = round(raw_avg, 2) if raw_avg is not None else 0.0

        recent_announcements_qs = Announcement.objects.filter(is_active=True).order_by('-created_at')[:3]
        recent_announcements = AnnouncementSerializer(recent_announcements_qs, many=True).data

        dashboard_data = {
            "status": {
                "oquvchilar_soni": total_students,
                "oqituvchilar_soni": total_teachers,
                "sinflar_soni": total_classes,
                "ortacha_baho": school_average_grade,

            },
            "oxirgi_3ta_elon": recent_announcements,
        }

        # serializer = AdminDashboardSerializer(raw_data)
        # serializer = AdminDashboardSerializer(dashboard_data)
        # return Response(serializer.data)
        return Response(dashboard_data)


class BulkGradeCreateAPIView(APIView):
    # permission_classes = [IsTeacher]


    def post(self, request):

        if not request.user.is_authenticated:
            return Response({"audenfikatsiyadn otmagansiz"})

        serializer = BulkGradeCreateSerializer(data=request.data)

        if serializer.is_valid():
            teacher = get_object_or_404(TeacherProfile, user = request.user)

            subject_id = serializer.validated_data['subject_id']
            date = serializer.validated_data['date']
            grades_data = serializer.validated_data['grades']

            if not teacher.subjects.filter(id=subject_id).exists():
                return Response({"detail": "Bu fan sizga biriktirilmagan"}, status=status.HTTP_403_FORBIDDEN)

            student_ids = {item['student_id'] for item in grades_data}
            if StudentProfile.objects.filter(id__in=student_ids).count() != len(student_ids):
                return Response({"detail": "Ba'zi o'quvchilar topilmadi"}, status=status.HTTP_400_BAD_REQUEST)

            # grades_to_create = []
            grades_to_create = [
                Grade(
                    student_id=item['student_id'],
                    teacher=teacher,
                    subject_id=subject_id,
                    date=date,
                    grade=item['grade'],
                    comment=item.get('comment', ''),
                ) for item in grades_data
            ]

            with transaction.atomic():
                Grade.objects.bulk_create(grades_to_create)

                for item in grades_data:
                    transaction.on_commit(
                        lambda item=item: send_grade_notification_task.delay(
                            student_id=item['student_id'],
                            subject_id=subject_id,
                            grade_value=item['grade']
                        )
                    )

            # for item in grades_date:
            #     grades_to_create.append(
            #         Grade(
            #             student_id = item['student_id'],
            #             teacher = teacher,
            #             subject_id=subject_id,
            #             date = date,
            #             grade = item['grade'],
            #             # comment = item['comment'],
            #             comment = item.get('comment', ''),
            #         )
            #
            #     )

            # Grade.objects.bulk_create(grades_to_create)
            # celery
            # for item in grades_date:
            #     send_grade_notification_task.delay(
            #         student_id = item['student_id'],
            #         # subject_id = item['subject_id'],
            #         subject_id=subject_id,
            #         grade_value = item['grade']
            #     )

            return Response({"detail": "Baholar muvaffaqiyatli saqlandi"}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SingleAttendanceAPIView(APIView):
    # permission_classes = [IsStaff]

    def post(self, request):
        serializer = SingleAttendanceSerializer(data=request.data)

        if serializer.is_valid():
            teacher = TeacherProfile.objects.filter(user=request.user).first()
            subject = serializer.validated_data['subject']

            if teacher and not teacher.subjects.filter(id=subject.id).exists():
                return Response({"detail": "Bu fan sizga biriktirilmagan"}, status=status.HTTP_403_FORBIDDEN)

            # serializer.save()
            attendance = serializer.save(teacher=teacher)

            # celery
            # if attendance.status in ['absent', 'late']:
            #     send_attendance_notification_task.delay(
            #         student_id = attendance.student_id,
            #         date = str(attendance.date),
            #         student = attendance.student
            #     )

            if attendance.status in [Attendance.Status.ABSENT, Attendance.Status.LATE]:
                send_attendance_notification_task.apply_async(
                    kwargs={
                        'student_id': attendance.student_id,
                        'date': str(attendance.date),
                        'status': attendance.status,
                    },
                    countdown=60,
                    expires=3600,
                )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubjectViewSet(viewsets.ModelViewSet):
    # permission_classes = [IsAdminOrReadOnly]

    # def get_queryset(self):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer

class SchoolClassViewSet(viewsets.ModelViewSet):
    # permission_classes = [IsAdminOrReadOnly]
    queryset = SchoolClass.objects.all()
    serializer_class = SchoolClassSerializer


class TeacherProfileViewSet(viewsets.ModelViewSet):
    queryset = TeacherProfile.objects.select_related('user', 'is_class_teacher').prefetch_related('subjects')
    # permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):

        if self.action in ['create', 'update', 'partial_update']:
            return TeacherProfileCreateSerializer

        # else:
        #     permission_classes = [IsAuthenticated]
        #
        # return [permission() for permission in permission_classes]
        return TeacherProfileSerializer


class StudentProfileViewSet(viewsets.ModelViewSet):
    queryset = StudentProfile.objects.select_related('user', 'school_class')

    # permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        qs = StudentProfile.objects.all()
        # if user.is_superuser or user.role in (User.Role.ADMIN, User.Role.TEACHER):
        #     return qs
        # if user.role == User.Role.PARENT:
        #     return qs.filter(parents__user=user)
        # return qs.filter(user=user)

        if not user.is_authenticated:
            return qs.none()

        if user.is_superuser or getattr(user, 'role', None) in ('admin', 'teacher'): # yoki User.Role.ADMIN
            return qs

        return qs.filter(user=user)

    def get_serializer_class(self):

        if self.action in ['create', 'update', 'partial_update']:
            return StudentProfileCreateSerializer

        return StudentProfileSerializer


class ParentProfileViewSet(viewsets.ModelViewSet):

    queryset = ParentProfile.objects.select_related('user').prefetch_related('children', 'children__user')

    # permission_classes = [IsAdmin]

    def get_serializer_class(self):

        if self.action in ['create', 'update', 'partial_update']:
            return ParentProfileCreateSerializer

        return ParentProfileSerializer


class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.select_related('school_class', 'subject', 'teacher__user')
    serializer_class = ScheduleSerializer
    # permission_classes = [IsAdminOrReadOnly]

#
# class ExamViewSet(viewsets.ModelViewSet):
#     queryset = Exam.objects.select_related('school_class', 'subject')
#     serializer_class = ExamSerializer
#     permission_classes = [IsAuthenticated]


class AnnouncementViewSet(viewsets.ModelViewSet):
    queryset = Announcement.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = AnnouncementSerializer
    # permission_classes = [IsAdminOrReadOnly]
    #
    # def perform_create(self, serializer):
    #     announcement = serializer.save()
    #     transaction.on_commit(lambda: send_announcement_task.delay(announcement.id))




class AdminDashboardAPIView(APIView):

    def get(self, request):

        student_count = StudentProfile.objects.count()
        teacher_count = TeacherProfile.objects.count()
        total_clases = SchoolClass.objects.count()

        avg_dict = Grade.objects.aggregate(avg=Avg('grade'))
        raw_avg = avg_dict['avg']
        school_average_grade = round(raw_avg, 2) if raw_avg is not None else 0.0

        recent_announcements = Announcement.objects.filter(is_active=True)[:3]

        top_classes = [
            {"class_name": "10-A", "average_grade": 4.5},
            {"class_name": "9-B", "average_grade": 4.3}
        ]

        # top_classes_qs = SchoolClass.objects.annotate(
        #     average_grade=Avg('students__grades__grade')
        # ).order_by('-average_grade')[:2]
        #
        # top_classes = [
        #     {"class_name": c.name, "average_grade": round(c.average_grade, 2)}
        #     for c in top_classes_qs if c.average_grade
        # ]

        data = {
            "total_students": student_count,
            "total_teachers": teacher_count,
            "total_classes": total_clases,
            "today_attendance_percentage": 92.5,
            "school_average_grade": school_average_grade,
            "recent_announcements": recent_announcements,
            "top_performing_classes": top_classes
        }

        serializer = AdminDashboardSerializer(data)
        return Response(serializer.data)





class StudentAnalyticsAPIView(APIView):
    def get(self, request, student_id):
        try:
            student = StudentProfile.objects.get(pk=student_id)
        except StudentProfile.DoesNotExist:
            return Response({"oquvchi topilmadi"})

        grades = student.grades.all()
        avg_grade = grades.aggregate(Avg('grade'))['grade__avg'] or 0.0
        total_grades = grades.count()

        attendances = student.attendances.all()
        total_lessons = attendances.count()
        present_count = attendances.filter(status='PRESENT').count()
        absent_count = attendances.filter(status='ABSENT').count()
        late_count = attendances.filter(status='LATE').count()
        excused_count = attendances.filter(status='EXCUSED').count()

        attendance_percentage = (present_count / total_lessons * 100) if total_lessons > 0 else 0.0

        data = {
            "student_id": student.id,
            "student_name": student.user.get_full_name(),
            # "roll_number": getattr(student, 'roll_number', 1),
            "class_name": student.school_class.name if student.school_class else "",
            "average_grade": round(avg_grade, 2),
            "total_grades_count": total_grades,
            "total_lessons": total_lessons,
            "present_count": present_count,
            "absent_count": absent_count,
            "late_count": late_count,
            "excused_count": excused_count,
            "attendance_percentage": round(attendance_percentage, 1)
        }

        serializer = StudentAnalyticsSerializer(data)
        return Response(serializer.data)

















































































































# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status, viewsets
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.viewsets import ModelViewSet
#
# from django.db import transaction
# from django.db.models import Avg
# from django.shortcuts import get_object_or_404
#
# from .models import (
#     StudentProfile, TeacherProfile, ParentProfile,
#     Subject, SchoolClass, Grade, Attendance,
#     Announcement, Schedule
# )
# from .serializers import (
#     StudentProfileSerializer, TeacherProfileSerializer, ParentProfileSerializer,
#     SubjectSerializer, SchoolClassSerializer, GradeSerializer,
#     AnnouncementSerializer, ScheduleSerializer,
#     TeacherProfileCreateSerializer, StudentProfileCreateSerializer,
#     ParentProfileCreateSerializer, SingleAttendanceSerializer,
#     TeacherDashboardSerializer, BulkGradeCreateSerializer,
# )
# from .tasks import send_grade_notification_task, send_attendance_notification_task
#
#
# # class SingleAttendanceAPIView(APIView):
# #     def get(self, request, *args, **kwargs):
# #         return Response({"detail": "Ishlayapti"})
#
# # class StudentDashboardAPIView(APIView):
# #
# #     permission_classes = [IsAuthenticated]
# #
# #     def get(self, request):
# #         # user = request.user
# #         # student_profile = user.student_profile
# #         student_profile = get_object_or_404(StudentProfile.objects.select_related('school_class', 'user'),
# #             user = request.user
# #         )
# #         serializer = FullStudentDashboardSerializer(student_profile)
# #         return Response(serializer.data)
#
#
# class TeacherDashboardAPIView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     def get(self, request):
#
#         teacher_profile = get_object_or_404(TeacherProfile.objects.select_related('user', 'is_class_teacher').prefetch_related('subjects'), user = request.user)
#
#         # serializer = TeacherProfileSerializer(teacher_profile)
#         serializer = TeacherDashboardSerializer(teacher_profile)
#         return Response(serializer.data)
#
#
# class AdminDashboardAPIView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     def get(self, request):
#
#         # techer_profile = get_object_or_404(
#         #     TeacherProfile.objects.select_related('user', 'is_class_teacher').prefetch_related('subjects'),
#         #     user = request.user
#         # )
#
#         total_students = StudentProfile.objects.count()
#         total_teachers = TeacherProfile.objects.count()
#         total_classes = SchoolClass.objects.count()
#         # total_subjects = Subject.objects.count()
#         # avg_result = Grade.objects.aggregate(Avg('grade'))['grade__avg']
#         avg_dict = Grade.objects.aggregate(avg=Avg('grade'))
#         raw_avg = avg_dict['avg']
#         # school_average_grade = round(avg_result['grade__avg'], 2) if avg_result is not None else 0.0
#         school_average_grade = round(raw_avg, 2) if raw_avg is not None else 0.0
#
#         recent_announcements_qs = Announcement.objects.filter(is_active=True).order_by('-created_at')[:3]
#         recent_announcements = AnnouncementSerializer(recent_announcements_qs, many=True).data
#
#         dashboard_data = {
#             "status": {
#                 "oquvchilar_soni": total_students,
#                 "oqituvchilar_soni": total_teachers,
#                 "sinflar_soni": total_classes,
#                 "ortacha_baho": school_average_grade,
#
#             },
#             # "techer_profile": techer_profile,
#             "oxirgi_3ta_elon": recent_announcements,
#         }
#
#         # serializer = AdminDashboardSerializer(raw_data)
#         # serializer = AdminDashboardSerializer(dashboard_data)
#         # return Response(serializer.data)
#         return Response(dashboard_data)
#
#
# class BulkGradeCreateAPIView(APIView):
#     permission_classes = [IsAuthenticated]
#
#
#     def post(self, request):
#
#         serializer = BulkGradeCreateSerializer(data=request.data)
#
#         if serializer.is_valid():
#             teacher = get_object_or_404(TeacherProfile, user = request.user)
#
#             subject_id = serializer.validated_data['subject_id']
#             # date = serializer.validated_data['date']
#             grades_data = serializer.validated_data['grades']
#
#             # grades_to_create = []
#             grades_to_create = [
#                 Grade(
#                     student_id=item['student_id'],
#                     teacher=teacher,
#                     subject_id=subject_id,
#                     # date=date,
#                     grade=item['grade'],
#                     comment=item.get('comment', ''),
#                 ) for item in grades_data
#             ]
#
#
#             with transaction.atomic():
#                 Grade.objects.bulk_create(grades_to_create)
#
#                 for item in grades_data:
#                     transaction.on_commit(
#                         lambda item=item: send_grade_notification_task.delay(
#                             student_id=item['student_id'],
#                             subject_id=subject_id,
#                             grade_value=item['grade']
#                         )
#                     )
#
#             # for item in grades_date:
#             #     grades_to_create.append(
#             #         Grade(
#             #             student_id = item['student_id'],
#             #             teacher = teacher,
#             #             subject_id=subject_id,
#             #             date = date,
#             #             grade = item['grade'],
#             #             # comment = item['comment'],
#             #             comment = item.get('comment', ''),
#             #         )
#             #
#             #     )
#
#             # Grade.objects.bulk_create(grades_to_create)
#             # celery
#             # for item in grades_date:
#             #     send_grade_notification_task.delay(
#             #         student_id = item['student_id'],
#             #         # subject_id = item['subject_id'],
#             #         subject_id=subject_id,
#             #         grade_value = item['grade']
#             #     )
#
#             return Response({"detail": "Baholar muvaffaqiyatli saqlandi"}, status=status.HTTP_201_CREATED)
#
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#
# class SingleAttendanceAPIView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     def post(self, request):
#         serializer = SingleAttendanceSerializer(data=request.data)
#
#         if serializer.is_valid():
#             # serializer.save()
#             attendance = serializer.save()
#
#             # celery
#             # if attendance.status in ['absent', 'late']:
#             #     send_attendance_notification_task.delay(
#             #         student_id = attendance.student_id,
#             #         date = str(attendance.date),
#             #         student = attendance.student
#             #     )
#
#             if attendance.status in [Attendance.Status.ABSENT, Attendance.Status.LATE]:
#                 send_attendance_notification_task.apply_async(
#                     kwargs={
#                         'student_id': attendance.student_id,
#                         'date': str(attendance.date),
#                         'status': attendance.status,
#                     },
#                     countdown=60,
#                     expires=3600,
#                 )
#             return Response(serializer.data, status=201)
#         else:
#             return Response(serializer.errors, status=400)
#
#         # return Response(serializer.errors, status=400)
#
#
# class SubjectViewSet(viewsets.ModelViewSet):
#     permission_classes = [IsAuthenticated]
#
#     # def get_queryset(self):
#     queryset = Subject.objects.all()
#     serializer_class = SubjectSerializer
#
# class SchoolClassViewSet(viewsets.ModelViewSet):
#     permission_classes = [IsAuthenticated]
#     queryset = SchoolClass.objects.all()
#     serializer_class = SchoolClassSerializer
#
#
# class TeacherProfileViewSet(viewsets.ModelViewSet):
#     queryset = TeacherProfile.objects.select_related('user').prefetch_related('subjects')
#     permission_classes = [IsAuthenticated]
#
#     def get_serializer_class(self):
#
#         if self.action in ['create', 'update', 'partial_update']:
#             return TeacherProfileCreateSerializer
#
#         # else:
#         #     permission_classes = [IsAuthenticated]
#         #
#         # return [permission() for permission in permission_classes]
#         return TeacherProfileSerializer
#
#
# class StudentProfileViewSet(viewsets.ModelViewSet):
#     queryset = StudentProfile.objects.select_related('user', 'school_class')
#
#     permission_classes = [IsAuthenticated]
#
#     def get_serializer_class(self):
#
#         if self.action in ['create', 'update', 'partial_update']:
#             return StudentProfileCreateSerializer
#
#         return StudentProfileSerializer
#
#
# class ParentProfileViewSet(viewsets.ModelViewSet):
#     queryset = ParentProfile.objects.select_related('user').prefetch_related('children', 'children__user')
#
#     permission_classes = [IsAuthenticated]
#
#     def get_serializer_class(self):
#
#         if self.action in ['create', 'update', 'partial_update']:
#             return ParentProfileCreateSerializer
#
#         return ParentProfileSerializer
#
#
# class ScheduleViewSet(viewsets.ModelViewSet):
#     queryset = Schedule.objects.select_related('school_class', 'subject', 'teacher')
#     serializer_class = ScheduleSerializer
#     permission_classes = [IsAuthenticated]
#
# #
# # class ExamViewSet(viewsets.ModelViewSet):
# #     queryset = Exam.objects.select_related('school_class', 'subject')
# #     serializer_class = ExamSerializer
# #     permission_classes = [IsAuthenticated]
#
#
# class AnnouncementViewSet(viewsets.ModelViewSet):
#     queryset = Announcement.objects.filter(is_active=True).order_by('-created_at')
#     serializer_class = AnnouncementSerializer
#     permission_classes = [IsAuthenticated]