from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = 'student', 'Student'
        FACULTY = 'faculty', 'Faculty'
        ADMIN = 'admin', 'Administrator'
    class Branch(models.TextChoices):
        CSE = 'CSE', 'CSE'
        ECE = 'ECE', 'ECE'
        CSM = 'CSM', 'CSM'
        CSD = 'CSD', 'CSD'
        EEE = 'EEE', 'EEE'
        MEC = 'MEC', 'MEC'
        CHEM = 'CHEM', 'CHEM'
        CIVIL = 'CIVIL', 'CIVIL'
        CSC = 'CSC', 'CSC'
        IT = 'IT', 'IT'
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=12, choices=Role.choices, default=Role.STUDENT)
    branch = models.CharField(max_length=8, choices=Branch.choices, blank=True)
    email_verified = models.BooleanField(default=False)
    faculty_approved = models.BooleanField(default=False)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    def __str__(self):
        return self.email

class EmailOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_otps')
    code_digest = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    consumed_at = models.DateTimeField(null=True, blank=True)
