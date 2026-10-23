from django import forms
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
