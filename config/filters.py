import django_filters
from .models import *

# davomat filter

class AttendanceFilter(django_filters.FilterSet):
    from_date = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    to_date =  django_filters.DateFilter(field_name='date', lookup_expr='lte')

    school_class = django_filters.NumberFilter(field_name="student__school_class__id")
    class_name = django_filters.CharFilter(field_name="student__school_class__name", lookup_expr='iexact')

    student = django_filters.NumberFilter(field_name="student__id")
    subject = django_filters.NumberFilter(field_name="subject__id")
    status = django_filters.CharFilter(field_name="status")

    class Meta:
        model = Attendance
        fields = ['student', 'subject', 'status', 'from_date', 'to_date', 'school_class', 'class_name']


# baholar uchun filtr

class GradeFilter(django_filters.FilterSet):
    from_date = django_filters.DateFilter(field_name="date", lookup_expr='gte')
    to_date = django_filters.DateFilter(field_name="date", lookup_expr='lte')

    school_class = django_filters.NumberFilter(field_name="student__school_class__id")
    student = django_filters.NumberFilter(field_name="student__id")
    subject = django_filters.NumberFilter(field_name="subject__id")

    min_grade = django_filters.NumberFilter(field_name="grade", lookup_expr='gte')
    max_grade = django_filters.NumberFilter(field_name="grade", lookup_expr='lte')

    class Meta:
        model = Grade
        fields = ['student', 'subject', 'from_date', 'to_date', 'school_class', 'min_grade', 'max_grade']


# 3. O'quvchilar ro'yxatini filtrlash

class StudentFilter(django_filters.FilterSet):

    school_class = django_filters.NumberFilter(field_name="school_class__id")
    search = django_filters.CharFilter(method='filter_by_name')

    class Meta:
        model = StudentProfile
        fields = ['school_class']

    def filter_by_name(self, queryset, name, value):
        return queryset.filter(
            models.Q(user__first_name__icontains=value) |
            models.Q(user__last_name__icontains=value) |
            models.Q(user__username__icontains=value)
        )