from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    # StudentDashboardAPIView,
    TeacherDashboardAPIView,
    AdminDashboardAPIView,
    BulkGradeCreateAPIView,
    SingleAttendanceAPIView,
    UserCreateAPIView,
    SubjectViewSet,
    SchoolClassViewSet,
    TeacherProfileViewSet,
    StudentProfileViewSet,
    ParentProfileViewSet,
    ScheduleViewSet,
    # ExamViewSet,   # Exam modeli va viewset yo'q
    AnnouncementViewSet,
)

router = DefaultRouter()
router.register(r'subjects', SubjectViewSet, basename='subject')
router.register(r'classes', SchoolClassViewSet, basename='class')
router.register(r'teachers', TeacherProfileViewSet, basename='teacher')
router.register(r'students', StudentProfileViewSet, basename='student')
router.register(r'parents', ParentProfileViewSet, basename='parent')
router.register(r'schedules', ScheduleViewSet, basename='schedule')
# router.register(r'exams', ExamViewSet, basename='exam')
router.register(r'announcements', AnnouncementViewSet, basename='announcement')

urlpatterns = [
    path('', include(router.urls)),

    path('users/', UserCreateAPIView.as_view(), name='user-create'),

    # path('dashboard/student/', StudentDashboardAPIView.as_view(), name='student-dashboard'),
    path('dashboard/teacher/', TeacherDashboardAPIView.as_view(), name='teacher-dashboard'),
    path('dashboard/admin/', AdminDashboardAPIView.as_view(), name='admin-dashboard'),

    path('grades/bulk-create/', BulkGradeCreateAPIView.as_view(), name='bulk-grade-create'),
    path('attendance/', SingleAttendanceAPIView.as_view(), name='single-attendance'),
]