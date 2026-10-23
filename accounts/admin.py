from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import EmailOTP, User

@admin.register(User)
class CampusUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (('Campus Resolve', {'fields': ('role', 'branch', 'email_verified', 'faculty_approved')}),)
    list_display = ('email', 'username', 'role', 'branch', 'email_verified', 'faculty_approved', 'is_staff')
    list_filter = ('role', 'branch', 'email_verified', 'faculty_approved')
    ordering = ('email',)
admin.site.register(EmailOTP)
