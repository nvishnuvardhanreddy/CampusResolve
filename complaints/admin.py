from django.contrib import admin
from django import forms
from accounts.models import User
from .models import Complaint, ComplaintUpdate

class ComplaintAssignmentForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_unit'].help_text = 'Choose the department or service team responsible for this complaint.'
        self.fields['assigned_to'].label = 'Assigned faculty / staff'
        self.fields['assigned_to'].help_text = 'You can change the unit and assignee together. Choose faculty from the student’s department or the matching service account.'

    def clean(self):
        cleaned = super().clean()
        unit = cleaned.get('assigned_unit')
        assignee = cleaned.get('assigned_to')
        student = cleaned.get('student') or getattr(self.instance, 'student', None)
        if not assignee or not unit:
            return cleaned

        if unit == Complaint.AssignmentUnit.DEPARTMENT:
            valid = assignee.role == User.Role.FACULTY and assignee.faculty_approved and student is not None and assignee.branch == student.branch
        else:
            service_roles = {
                Complaint.AssignmentUnit.LIBRARY: (User.Role.LIBRARY,),
                Complaint.AssignmentUnit.FACILITIES: (User.Role.MAINTENANCE,),
                Complaint.AssignmentUnit.HOSTEL: (User.Role.MAINTENANCE,),
                Complaint.AssignmentUnit.TRANSPORT: (User.Role.MAINTENANCE,),
                Complaint.AssignmentUnit.IT_SUPPORT: (User.Role.MAINTENANCE,),
                Complaint.AssignmentUnit.ADMINISTRATION: (User.Role.ADMIN,),
                Complaint.AssignmentUnit.EXAMINATIONS: (User.Role.ADMIN,),
                Complaint.AssignmentUnit.ACCOUNTS: (User.Role.ADMIN,),
                Complaint.AssignmentUnit.STUDENT_SUPPORT: (User.Role.ADMIN,),
                Complaint.AssignmentUnit.ANTI_RAGGING: (User.Role.ADMIN,),
                Complaint.AssignmentUnit.OTHER: (User.Role.ADMIN,),
            }
            valid = assignee.role in service_roles.get(unit, ())
        if not valid:
            self.add_error('assigned_to', 'Choose an active, approved assignee that matches the selected unit and department.')
        return cleaned

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    form = ComplaintAssignmentForm
    list_display = ('reference', 'title', 'department', 'category', 'assigned_unit', 'assigned_to', 'status', 'updated_at')
    list_filter = ('student__branch', 'category', 'assigned_unit', 'status', 'assigned_to')
    list_editable = ('assigned_unit', 'status')
    fields = ('student', 'category', 'title', 'description', 'assigned_unit', 'assigned_to', 'status', 'resolution')
    search_fields = ('reference', 'title', 'student__email', 'student__first_name')

    @admin.display(description='Department', ordering='student__branch')
    def department(self, obj):
        return obj.student.branch

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'assigned_to':
            kwargs['queryset'] = User.objects.filter(
                role__in=(User.Role.FACULTY, User.Role.MAINTENANCE, User.Role.LIBRARY, User.Role.ADMIN),
                is_active=True,
            ).order_by('role', 'branch', 'first_name', 'email')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(ComplaintUpdate)
