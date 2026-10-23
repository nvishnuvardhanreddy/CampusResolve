from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import User

class VerifiedAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.email_verified:
            raise forms.ValidationError('Verify your email before signing in.', code='email_unverified')

class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, label='Full name')
    email = forms.EmailField()
    role = forms.ChoiceField(choices=[(User.Role.STUDENT, 'Student'), (User.Role.FACULTY, 'Faculty')])
    branch = forms.ChoiceField(choices=User.Branch.choices)
    class Meta:
        model = User
        fields = ('first_name', 'username', 'email', 'role', 'branch')
    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account already exists for this email address.')
        return email
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.role = self.cleaned_data['role']
        user.branch = self.cleaned_data['branch']
        if commit: user.save()
        return user
