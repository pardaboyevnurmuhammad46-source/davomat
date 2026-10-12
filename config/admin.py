from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, SchoolClass, Subject, TeacherProfile,
    StudentProfile, ParentProfile, Attendance, Grade
)


# 1. Custom User Admin Sozlamasi
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'get_full_name', 'role', 'phone', 'telegram_id', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'phone', 'telegram_id')
    ordering = ('username',)

    # User formasida qo'shimcha maydonlarni ko'rsatish
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Qo'shimcha ma'lumotlar", {'fields': ('role', 'phone', 'telegram_id')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Qo'shimcha ma'lumotlar", {'fields': ('role', 'phone', 'telegram_id')}),
    )


# 2. Sinf (Class) Admin Sozlamasi
@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'academic_year', 'get_student_count')
    search_fields = ('name', 'academic_year')
    list_filter = ('academic_year',)

    @admin.display(description="O'quvchilar soni")
    def get_student_count(self, obj):
        return obj.students.count()


# 3. Fanlar Admin Sozlamasi
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


# 4. Ustoz Profil Admin Sozlamasi
@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_class_teacher', 'get_subjects')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    list_filter = ('is_class_teacher', 'subjects')
    filter_horizontal = ('subjects',) # ManyToMany maydonni qulay tanlash paneli

    @admin.display(description='Fanlari')
    def get_subjects(self, obj):
        return ", ".join([s.name for s in obj.subjects.all()])


# 5. O'quvchi Profil Admin Sozlamasi
@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'school_class', 'roll_number')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'school_class__name')
    list_filter = ('school_class',)
    ordering = ('school_class', 'roll_number')


# 6. Ota-ona Profil Admin Sozlamasi
@admin.register(ParentProfile)
class ParentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_children')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    filter_horizontal = ('children',) # O'quvchilarni oson biriktirish uchun

    @admin.display(description="Farzandlari")
    def get_children(self, obj):
        return ", ".join([f"{c.user.get_full_name()} ({c.school_class.name})" for c.children in [obj.children.all()] for c in children])


# 7. Davomat (Attendance) Admin Sozlamasi
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'date', 'status', 'teacher')
    list_filter = ('status', 'date', 'subject', 'student__school_class')
    search_fields = ('student__user__first_name', 'student__user__last_name', 'remark')
    date_hierarchy = 'date' # Sana bo'yicha yuqorida qulay navigatsiya paneli chiqaradi
    list_editable = ('status',) # Admin panelning o'zidanoq statusni tezkor o'zgartirish


# 8. Baholar (Grade) Admin Sozlamasi
@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'grade', 'comment', 'teacher', 'date')
    list_filter = ('grade', 'subject', 'date', 'student__school_class')
    search_fields = ('student__user__first_name', 'student__user__last_name', 'comment')
    date_hierarchy = 'date'
    list_editable = ('grade',) # Bahoni tezkor o'zgartirish qulayligi