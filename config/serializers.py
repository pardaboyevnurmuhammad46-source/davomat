from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
# from django.utils.timezone import now
from django.utils.timezone import localdate
from .models import (
    User, SchoolClass, Subject, TeacherProfile,
    StudentProfile, ParentProfile, Attendance, Grade,
    Announcement, Schedule
)

DAYS = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]


# class ExamSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Exam
#         fields = '__all__'

# elonlar
class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = '__all__'
# fan
class SubjectSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subject
        fields = ['id','name']

# Sinflar
class SchoolClassSerializer(serializers.ModelSerializer):

    class Meta:
        model = SchoolClass
        fields = ['id','name']

# oqituvchi
class TeacherProfileSerializer(serializers.ModelSerializer):
    subjects = SubjectSerializer(many=True, read_only=True)
    is_class_teacher = SchoolClassSerializer(read_only=True)

    class Meta:
        model = TeacherProfile
        fields = ['id', 'subjects', 'is_class_teacher']

# oquvchi
class StudentProfileSerializer(serializers.ModelSerializer):

    school_class = SchoolClassSerializer(read_only=True)

    class Meta:
        # school_class = SchoolClassSerializer(read_only=True)

        model = StudentProfile
        fields = ['id','user', 'roll_number', 'school_class']

# ota - ona
class ParentProfileSerializer(serializers.ModelSerializer):
    children = StudentProfileSerializer(many=True, read_only=True)

    class Meta:
        model = ParentProfile
        fields = ['id', 'children']

# user
class UserProfileSerializer(serializers.ModelSerializer):

    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'profile']

    def get_profile(self, obj):
        if obj.role == User.Role.TEACHER and hasattr(obj, 'teacher_profile'):
            return TeacherProfileSerializer(obj.teacher_profile).data
        elif obj.role == User.Role.STUDENT and hasattr(obj, 'student_profile'):
            return StudentProfileSerializer(obj.student_profile).data
        elif obj.role == User.Role.PARENT and hasattr(obj, 'parent_profile'):
            return ParentProfileSerializer(obj.parent_profile).data
        return None


# token
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)
        # user_serializer = UserSerializer(self.user)
        user_serializer = UserProfileSerializer(self.user)
        data['user'] = user_serializer.data
        return data

# yangi user
class UserCreateSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only = True, max_length = 64, min_length = 8)

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'first_name', 'last_name', 'role', 'phone', 'telegram_id']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        # user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user

# oqituvchi profil qoshshish
class TeacherProfileCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherProfile
        fields = ['id', 'user', 'subjects', 'is_class_teacher']

    # def to_representation(self, instance):
    #     representation = {}
    #     representation['subjects'] = SubjectSerializer(instance.subjects.all(), many=True).data
    #     return representation

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # representation['subjects'] = SubjectSerializer(instance.subjects, many=True).data
        representation['subjects'] = SubjectSerializer(instance.subjects.all(), many=True).data
        if instance.is_class_teacher:
            # representation['is_class_teacher'] = SchoolClassSerializer(instance.is_class_teacher).data
            representation['is_class_teacher'] = SchoolClassSerializer(instance.is_class_teacher).data
        return representation


class StudentProfileCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = '__all__'

class ParentProfileCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentProfile
        fields = '__all__'
# davomat
class SingleAttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        # fields = '__all__'
        fields = ['id', 'student', 'subject', 'teacher', 'date', 'status', 'remark']
        read_only_fields = ['teacher']


class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = '__all__'


class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        # fields = ['id', 'subject', 'time', 'room', 'teacher_name']
        # school_class, teacher, day qo'shildi, aks holda POST qilganda xato chiqadi
        fields = ['id', 'school_class', 'subject', 'teacher', 'day', 'time', 'room', 'teacher_name']


# class FullStudentDashboardSerializer(serializers.ModelSerializer):
#     student_name = serializers.CharField(source = 'user.get_full_name')
#     class_name = serializers.CharField(source = 'school_class.name')
#
#     today_schedule = serializers.SerializerMethodField()
#     attendance_summary = serializers.SerializerMethodField()
#     recent_grades = serializers.SerializerMethodField()
#     upcoming_exams = serializers.SerializerMethodField()
#     announcements = serializers.SerializerMethodField()
#
#     class Meta:
#         model = StudentProfile
#         fields = [
#             'id', 'student_name', 'class_name', 'today_schedule',
#             'attendance_summary', 'recent_grades', 'upcoming_exams', 'announcements'
#         ]
#
#     def get_today_schedule(self, obj):
#
#         return ScheduleSerializer(obj.school_class.schedules.filter(day="TODAY"), many=True).data
#
#     def get_attendance_summary(self, obj):
#         total = obj.attendances.count()
#         present = obj.attendances.filter(status='PRESENT').count()
#         return {
#             "total_lessons": total,
#             "percentage": round((present / total * 100), 1) if total > 0 else 100
#         }
#
#     def get_recent_grades(self, obj):
#         return GradeSerializer(obj.grades.order_by('-date')[:5], many=True).data
#
#     # def get_upcoming_exams(self, obj):
#     #     return ExamSerializer(Exam.objects.filter(school_class=obj.school_class, date__gte=now()), many=True).data
#
#     def get_announcements(self, obj):
#         return AnnouncementSerializer(Announcement.objects.filter(is_active=True)[:3], many=True).data

class BulkGradeSerializer(serializers.Serializer):
    grades = GradeSerializer(many=True)
    # grades = GradeCreateSerializer()


# oqituvchining shaxsiy kabineti
class TeacherDashboardSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='user.get_full_name', read_only=True)
    is_class_teacher_of = serializers.CharField(source='is_class_teacher.name', read_only=True, default=None)

    today_lessons = serializers.SerializerMethodField()
    my_subjects = SubjectSerializer(source='subjects', many=True, read_only=True)
    recent_graded_students = serializers.SerializerMethodField()
    announcements = serializers.SerializerMethodField()

    class Meta:
        model = TeacherProfile
        fields = [
            'id', 'teacher_name', 'is_class_teacher_of',
            'my_subjects', 'today_lessons', 'recent_graded_students', 'announcements'
        ]

    # def get_today_lessons(self, obj):
    #     if hasattr(obj, 'schedules'):
    #         return ScheduleSerializer(obj.schedules.filter(day="TODAY"), many=True).data
    #     return []


    def get_today_lessons(self, obj):
        today = DAYS[localdate().weekday()]
        return ScheduleSerializer(obj.schedules.filter(day=today), many=True).data

    def get_recent_graded_students(self, obj):
        grades = Grade.objects.filter(teacher=obj).order_by('-date')[:5]
        return GradeSerializer(grades, many=True).data

    def get_announcements(self, obj):
        return AnnouncementSerializer(Announcement.objects.filter(is_active=True)[:3], many=True).data

# statistika
class AdminDashboardSerializer(serializers.Serializer):
    total_students = serializers.IntegerField()
    total_teachers = serializers.IntegerField()
    total_classes = serializers.IntegerField()
    today_attendance_percentage = serializers.FloatField()
    school_average_grade = serializers.FloatField()
    recent_announcements = AnnouncementSerializer(many=True)
    top_performing_classes = serializers.ListField(child=serializers.DictField())

#1ta oquvchi statistika
class StudentAnalyticsSerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    student_name = serializers.CharField()
    roll_number = serializers.IntegerField()
    class_name = serializers.CharField()
    average_grade = serializers.FloatField()
    total_grades_count = serializers.IntegerField()
    total_lessons = serializers.IntegerField()
    present_count = serializers.IntegerField()
    absent_count = serializers.IntegerField()
    late_count = serializers.IntegerField()
    excused_count = serializers.IntegerField()
    attendance_percentage = serializers.FloatField()


# butun sinf ststitika
class ClassAnalyticsSerializer(serializers.Serializer):
    class_id = serializers.IntegerField()
    class_name = serializers.CharField()
    academic_year = serializers.CharField()
    students_count = serializers.IntegerField()
    class_average_grade = serializers.FloatField()
    total_attendances_recorded = serializers.IntegerField()
    total_absent_count = serializers.IntegerField()
    total_late_count = serializers.IntegerField()
    overall_attendance_percentage = serializers.FloatField()



# baxo
class SingleGradeItemSerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    grade = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")

# butun sinf uchun
class BulkGradeCreateSerializer(serializers.Serializer):
    subject_id = serializers.IntegerField()
    date = serializers.DateField(default=localdate)
    grades = SingleGradeItemSerializer(many=True, allow_empty=False)





















































































# from rest_framework import serializers
# from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
# # from django.utils.timezone import now
# from django.utils.timezone import localdate
# from .models import (
#     User, SchoolClass, Subject, TeacherProfile,
#     StudentProfile, ParentProfile, Attendance, Grade,
#     Announcement, Schedule
# )
#
# DAYS = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]
#
#
# # class ExamSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = Exam
# #         fields = '__all__'
#
# class AnnouncementSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Announcement
#         fields = '__all__'
#
# class SubjectSerializer(serializers.ModelSerializer):
#
#     class Meta:
#         model = Subject
#         fields = ['id','name']
#
# class SchoolClassSerializer(serializers.ModelSerializer):
#
#     class Meta:
#         model = SchoolClass
#         fields = ['id','name']
#
# class TeacherProfileSerializer(serializers.ModelSerializer):
#     subjects = SubjectSerializer(many=True, read_only=True)
#     is_class_teacher = SchoolClassSerializer(read_only=True)
#
#     class Meta:
#         model = TeacherProfile
#         fields = ['id', 'subjects', 'is_class_teacher']
#
#
# class StudentProfileSerializer(serializers.ModelSerializer):
#
#     school_class = SchoolClassSerializer(read_only=True)
#
#     class Meta:
#         # school_class = SchoolClassSerializer(read_only=True)
#
#         model = StudentProfile
#         fields = ['id','user', 'roll_number', 'school_class']
#
#
# class ParentProfileSerializer(serializers.ModelSerializer):
#     children = StudentProfileSerializer(many=True, read_only=True)
#
#     class Meta:
#         model = ParentProfile
#         fields = ['id', 'children']
#
#
# class UserProfileSerializer(serializers.ModelSerializer):
#
#     profile = serializers.SerializerMethodField()
#
#     class Meta:
#         model = User
#         fields = ['id', 'username', 'first_name', 'last_name', 'email', 'profile']
#
#     def get_profile(self, obj):
#         if obj.role == User.Role.TEACHER and hasattr(obj, 'teacher_profile'):
#             return TeacherProfileSerializer(obj.teacher_profile).data
#         elif obj.role == User.Role.STUDENT and hasattr(obj, 'student_profile'):
#             return StudentProfileSerializer(obj.student_profile).data
#         elif obj.role == User.Role.PARENT and hasattr(obj, 'parent_profile'):
#             return ParentProfileSerializer(obj.parent_profile).data
#         return None
#
#
#
# class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
#
#     def validate(self, attrs):
#         data = super().validate(attrs)
#         # user_serializer = UserSerializer(self.user)
#         user_serializer = UserProfileSerializer(self.user)
#         data['user'] = user_serializer.data
#         return data
#
#
# class UserCreateSerializer(serializers.ModelSerializer):
#
#     password = serializers.CharField(write_only = True, max_length = 64, min_length = 2)
#
#     class Meta:
#         model = User
#         fields = ['id', 'username', 'password', 'first_name', 'last_name', 'role', 'phone', 'telegram_id']
#
#     def create(self, validated_data):
#         password = validated_data.pop('password')
#         user = User(**validated_data)
#         # user = User.objects.create(**validated_data)
#         user.set_password(password)
#         user.save()
#         return user
#
#
# class TeacherProfileCreateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TeacherProfile
#         fields = ['id', 'user', 'subjects', 'is_class_teacher']
#
#     # def to_representation(self, instance):
#     #     representation = {}
#     #     representation['subjects'] = SubjectSerializer(instance.subjects.all(), many=True).data
#     #     return representation
#
#     def to_representation(self, instance):
#         representation = super().to_representation(instance)
#         # representation['subjects'] = SubjectSerializer(instance.subjects, many=True).data
#         representation['subjects'] = SubjectSerializer(instance.subjects.all(), many=True).data
#         if instance.is_class_teacher:
#             # representation['is_class_teacher'] = SchoolClassSerializer(instance.is_class_teacher).data
#             representation['is_class_teacher'] = SchoolClassSerializer(instance.is_class_teacher).data
#         return representation
#
#
# class StudentProfileCreateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = StudentProfile
#         fields = '__all__'
#
# class ParentProfileCreateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ParentProfile
#         fields = '__all__'
#
# class SingleAttendanceSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Attendance
#         fields = '__all__'
#
#
# class GradeSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Grade
#         fields = '__all__'
#
#
# class ScheduleSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Schedule
#         # fields = ['id', 'subject', 'time', 'room', 'teacher_name']
#         fields = ['id', 'school_class', 'subject', 'teacher', 'day', 'time', 'room', 'teacher_name']
#
#
# # class FullStudentDashboardSerializer(serializers.ModelSerializer):
# #     student_name = serializers.CharField(source = 'user.get_full_name')
# #     class_name = serializers.CharField(source = 'school_class.name')
# #
# #     today_schedule = serializers.SerializerMethodField()
# #     attendance_summary = serializers.SerializerMethodField()
# #     recent_grades = serializers.SerializerMethodField()
# #     upcoming_exams = serializers.SerializerMethodField()
# #     announcements = serializers.SerializerMethodField()
# #
# #     class Meta:
# #         model = StudentProfile
# #         fields = [
# #             'id', 'student_name', 'class_name', 'today_schedule',
# #             'attendance_summary', 'recent_grades', 'upcoming_exams', 'announcements'
# #         ]
# #
# #
# #     def get_today_schedule(self, obj):
# #
# #         return ScheduleSerializer(obj.school_class.schedules.filter(day="TODAY"), many=True).data
# #
# #     def get_attendance_summary(self, obj):
# #         total = obj.attendances.count()
# #         present = obj.attendances.filter(status='PRESENT').count()
# #         return {
# #             "total_lessons": total,
# #             "percentage": round((present / total * 100), 1) if total > 0 else 100
# #         }
# #
# #     def get_recent_grades(self, obj):
# #         return GradeSerializer(obj.grades.order_by('-date')[:5], many=True).data
# #
# #     # def get_upcoming_exams(self, obj):
# #     #     return ExamSerializer(Exam.objects.filter(school_class=obj.school_class, date__gte=now()), many=True).data
# #
# #     def get_announcements(self, obj):
# #         return AnnouncementSerializer(Announcement.objects.filter(is_active=True)[:3], many=True).data
#
# class BulkGradeSerializer(serializers.Serializer):
#     grades = GradeSerializer(many=True)
#     # grades = GradeCreateSerializer()
#
#
# class TeacherDashboardSerializer(serializers.ModelSerializer):
#     teacher_name = serializers.CharField(source='user.get_full_name', read_only=True)
#     is_class_teacher_of = serializers.CharField(source='is_class_teacher.name', read_only=True, default=None)
#
#     today_lessons = serializers.SerializerMethodField()
#     my_subjects = SubjectSerializer(source='subjects', many=True, read_only=True)
#     recent_graded_students = serializers.SerializerMethodField()
#     announcements = serializers.SerializerMethodField()
#
#     class Meta:
#         model = TeacherProfile
#         fields = [
#             'id', 'teacher_name', 'is_class_teacher_of',
#             'my_subjects', 'today_lessons', 'recent_graded_students', 'announcements'
#         ]
#
#     # def get_today_lessons(self, obj):
#     #     if hasattr(obj, 'schedules'):
#     #         return ScheduleSerializer(obj.schedules.filter(day="TODAY"), many=True).data
#     #     return []
#
#     def get_today_lessons(self, obj):
#         today = DAYS[localdate().weekday()]
#         return ScheduleSerializer(obj.schedules.filter(day=today), many=True).data
#
#     def get_recent_graded_students(self, obj):
#         grades = Grade.objects.filter(teacher=obj).order_by('-date')[:5]
#         return GradeSerializer(grades, many=True).data
#
#     def get_announcements(self, obj):
#         return AnnouncementSerializer(Announcement.objects.filter(is_active=True)[:3], many=True).data
#
#
# class AdminDashboardSerializer(serializers.Serializer):
#     total_students = serializers.IntegerField()
#     total_teachers = serializers.IntegerField()
#     total_classes = serializers.IntegerField()
#     today_attendance_percentage = serializers.FloatField()
#     school_average_grade = serializers.FloatField()
#     recent_announcements = AnnouncementSerializer(many=True)
#     top_performing_classes = serializers.ListField(child=serializers.DictField())
#
#
# class StudentAnalyticsSerializer(serializers.Serializer):
#     student_id = serializers.IntegerField()
#     student_name = serializers.CharField()
#     roll_number = serializers.IntegerField()
#     class_name = serializers.CharField()
#     average_grade = serializers.FloatField()
#     total_grades_count = serializers.IntegerField()
#     total_lessons = serializers.IntegerField()
#     present_count = serializers.IntegerField()
#     absent_count = serializers.IntegerField()
#     late_count = serializers.IntegerField()
#     excused_count = serializers.IntegerField()
#     attendance_percentage = serializers.FloatField()
#
#
# class ClassAnalyticsSerializer(serializers.Serializer):
#     class_id = serializers.IntegerField()
#     class_name = serializers.CharField()
#     academic_year = serializers.CharField()
#     students_count = serializers.IntegerField()
#     class_average_grade = serializers.FloatField()
#     total_attendances_recorded = serializers.IntegerField()
#     total_absent_count = serializers.IntegerField()
#     total_late_count = serializers.IntegerField()
#     overall_attendance_percentage = serializers.FloatField()
#
#
#
#
# class SingleGradeItemSerializer(serializers.Serializer):
#     student_id = serializers.IntegerField()
#     grade = serializers.IntegerField(min_value=1, max_value=5)
#     comment = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
#
#
# class BulkGradeCreateSerializer(serializers.Serializer):
#     subject_id = serializers.IntegerField()
#     # date = serializers.DateField(default=now)
#     grades = SingleGradeItemSerializer(many=True)