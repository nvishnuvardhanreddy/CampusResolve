from django import forms
from accounts.models import User
from .models import Complaint, ComplaintUpdate
class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['category', 'title', 'description']
        widgets = {'description': forms.Textarea(attrs={'rows': 5})}
class UpdateForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), label='Progress note')
    visible_to_student = forms.BooleanField(required=False, initial=True, label='Visible to student')
    status = forms.ChoiceField(choices=Complaint.Status.choices)
    resolution = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}))

class ComplaintAssignmentForm(forms.ModelForm):
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(
            role__in=(User.Role.FACULTY, User.Role.MAINTENANCE, User.Role.LIBRARY, User.Role.ADMIN),
            is_active=True,
        ).order_by('role', 'branch', 'first_name', 'email'),
        required=False, label='Faculty / service staff', empty_label='Not assigned yet',
    )

    class Meta:
        model = Complaint
        fields = ('assigned_unit', 'assigned_to')

    def clean(self):
        cleaned = super().clean()
        unit, assignee = cleaned.get('assigned_unit'), cleaned.get('assigned_to')
        if not unit or not assignee:
            return cleaned
        if unit == Complaint.AssignmentUnit.DEPARTMENT:
            valid = assignee.role == User.Role.FACULTY and assignee.faculty_approved and assignee.branch == self.instance.student.branch
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
            self.add_error('assigned_to', 'Select an assignee that matches the chosen unit and the student’s department.')
        return cleaned
