import uuid
from django.conf import settings
from django.db import models

class Complaint(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = 'submitted', 'Submitted'
        REVIEW = 'review', 'Under review'
        PROGRESS = 'progress', 'In progress'
        RESOLVED = 'resolved', 'Resolved'
        CLOSED = 'closed', 'Closed'
    CATEGORIES = [
        ('academics','Academics'), ('facilities','Facilities'),
        ('harassment','Harassment'), ('ragging','Ragging / Bullying'),
        ('administration','Administration'), ('other','Other'),
    ]
    reference = models.CharField(max_length=12, unique=True, editable=False)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='complaints')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_complaints')
    category = models.CharField(max_length=60, choices=CATEGORIES)
    title = models.CharField(max_length=160)
    description = models.TextField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.SUBMITTED)
    resolution = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = uuid.uuid4().hex[:10].upper()
        super().save(*args, **kwargs)
    def __str__(self): return f'{self.reference} — {self.title}'

class ComplaintUpdate(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='updates')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    message = models.TextField()
    visible_to_student = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['created_at']
