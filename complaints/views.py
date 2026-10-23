from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from .forms import ComplaintForm, UpdateForm
from .models import Complaint, ComplaintUpdate

ACTIVE_STATUSES = (Complaint.Status.SUBMITTED, Complaint.Status.REVIEW, Complaint.Status.PROGRESS)
COMPLETED_STATUSES = (Complaint.Status.RESOLVED, Complaint.Status.CLOSED)

def home(request): return render(request, 'home.html')

def dashboard_scope(user):
    all_cases = user.is_superuser or user.role == 'admin'
    if all_cases or user.role == 'faculty':
        return Complaint.objects.all(), all_cases
    return Complaint.objects.filter(student=user), False

def get_counts(user):
    qs, all_cases = dashboard_scope(user)
    row = qs.aggregate(
        total=Count('id'),
        active=Count('id', filter=Q(status__in=ACTIVE_STATUSES)),
        submitted=Count('id', filter=Q(status=Complaint.Status.SUBMITTED)),
        review=Count('id', filter=Q(status=Complaint.Status.REVIEW)),
        progress=Count('id', filter=Q(status=Complaint.Status.PROGRESS)),
        completed=Count('id', filter=Q(status__in=COMPLETED_STATUSES)),
    )
    row['scope'] = 'college' if all_cases or user.role == 'faculty' else 'personal'
    return row

@login_required
def dashboard(request):
    if request.user.role == 'faculty' and not request.user.faculty_approved:
        return render(request, 'complaints/faculty_pending.html')
    qs, all_cases = dashboard_scope(request.user)
    if request.user.role == 'faculty':
        qs = Complaint.objects.filter(Q(assigned_to=request.user) | Q(student=request.user))
    qs = qs.select_related('student','assigned_to').order_by('-created_at')
    return render(request, 'complaints/dashboard.html', {
        'complaints': qs, 'counts': get_counts(request.user),
        'can_submit': request.user.role in ('student', 'faculty'),
        'all_cases': all_cases,
    })

@login_required
def dashboard_counts(request):
    if request.user.role == 'faculty' and not request.user.faculty_approved:
        return JsonResponse({'error': 'Faculty account approval is pending.'}, status=403)
    return JsonResponse(get_counts(request.user))

@login_required
def create_complaint(request):
    if request.user.role == 'faculty' and not request.user.faculty_approved:
        messages.error(request, 'Your faculty account is awaiting administrator approval.')
        return redirect('dashboard')
    if request.method == 'POST':
        form = ComplaintForm(request.POST)
        if form.is_valid():
            complaint = form.save(commit=False); complaint.student = request.user; complaint.save()
            messages.success(request, f'Complaint submitted. Reference: {complaint.reference}')
            return redirect('complaint_detail', pk=complaint.pk)
    else: form = ComplaintForm()
    return render(request, 'complaints/complaint_form.html', {'form': form})

@login_required
def complaint_detail(request, pk):
    complaint = get_object_or_404(Complaint.objects.select_related('student','assigned_to').prefetch_related('updates__author'), pk=pk)
    faculty = request.user.role == 'faculty' and request.user.faculty_approved
    allowed = request.user.is_superuser or request.user.role == 'admin' or complaint.student_id == request.user.id or (faculty and complaint.assigned_to_id == request.user.id)
    if not allowed: return render(request, '403.html', status=403)
    staff_access = request.user.is_superuser or request.user.role == 'admin' or (faculty and complaint.assigned_to_id == request.user.id)
    if request.method == 'POST' and staff_access:
        form = UpdateForm(request.POST)
        if form.is_valid():
            ComplaintUpdate.objects.create(complaint=complaint, author=request.user, message=form.cleaned_data['message'], visible_to_student=form.cleaned_data['visible_to_student'])
            complaint.status = form.cleaned_data['status']
            complaint.resolution = form.cleaned_data['resolution']
            complaint.save(update_fields=['status','resolution','updated_at'])
            messages.success(request, 'Complaint status and update saved.')
            return redirect('complaint_detail', pk=pk)
    else: form = UpdateForm(initial={'status': complaint.status, 'resolution': complaint.resolution})
    updates = complaint.updates.all()
    if complaint.student_id == request.user.id: updates = updates.filter(visible_to_student=True)
    return render(request, 'complaints/complaint_detail.html', {'complaint': complaint, 'updates': updates, 'form': form, 'staff_access': staff_access})
