from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from .forms import ComplaintAssignmentForm, ComplaintForm, UpdateForm
from .models import Complaint, ComplaintUpdate

ACTIVE_STATUSES = (Complaint.Status.SUBMITTED, Complaint.Status.REVIEW, Complaint.Status.PROGRESS)
COMPLETED_STATUSES = (Complaint.Status.RESOLVED, Complaint.Status.CLOSED)

DEFAULT_ASSIGNMENT_UNIT = {
    'academics': Complaint.AssignmentUnit.DEPARTMENT,
    'library': Complaint.AssignmentUnit.LIBRARY,
    'facilities': Complaint.AssignmentUnit.FACILITIES,
    'administration': Complaint.AssignmentUnit.ADMINISTRATION,
    'hostel': Complaint.AssignmentUnit.HOSTEL,
    'transport': Complaint.AssignmentUnit.TRANSPORT,
    'it_support': Complaint.AssignmentUnit.IT_SUPPORT,
    'examinations': Complaint.AssignmentUnit.EXAMINATIONS,
    'accounts': Complaint.AssignmentUnit.ACCOUNTS,
    'harassment': Complaint.AssignmentUnit.STUDENT_SUPPORT,
    'ragging': Complaint.AssignmentUnit.ANTI_RAGGING,
    'other': Complaint.AssignmentUnit.OTHER,
}

def home(request): return render(request, 'home.html')

def dashboard_scope(user):
    if user.is_superuser or user.role == 'admin' or user.role == 'faculty':
        return Complaint.objects.all(), 'college'
    if user.role in ('student', 'hod'):
        return Complaint.objects.filter(student__branch=user.branch), 'department'
    if user.role in ('maintenance', 'library'):
        return Complaint.objects.filter(assigned_to=user), 'assigned'
    return Complaint.objects.filter(student=user), 'personal'

def get_counts(user):
    qs, scope = dashboard_scope(user)
    row = qs.aggregate(
        total=Count('id'),
        active=Count('id', filter=Q(status__in=ACTIVE_STATUSES)),
        submitted=Count('id', filter=Q(status=Complaint.Status.SUBMITTED)),
        review=Count('id', filter=Q(status=Complaint.Status.REVIEW)),
        progress=Count('id', filter=Q(status=Complaint.Status.PROGRESS)),
        completed=Count('id', filter=Q(status__in=COMPLETED_STATUSES)),
    )
    row['scope'] = scope
    return row

@login_required
def dashboard(request):
    if request.user.role == 'faculty' and not request.user.faculty_approved:
        return render(request, 'complaints/faculty_pending.html')
    department_summaries = None
    if request.user.role == 'student':
        department_summaries = Complaint.objects.filter(
            student__branch=request.user.branch,
        ).order_by('-created_at')
        qs = Complaint.objects.filter(student=request.user)
    elif request.user.role == 'hod':
        qs = Complaint.objects.filter(student__branch=request.user.branch)
    elif request.user.role == 'faculty':
        qs = Complaint.objects.filter(Q(assigned_to=request.user) | Q(student=request.user))
    elif request.user.role in ('maintenance', 'library'):
        qs = Complaint.objects.filter(assigned_to=request.user)
    else:
        qs = Complaint.objects.all()
    qs = qs.select_related('student','assigned_to').order_by('-created_at')
    return render(request, 'complaints/dashboard.html', {
        'complaints': qs, 'counts': get_counts(request.user),
        'department_summaries': department_summaries,
        'can_submit': request.user.role == 'student' or (request.user.role == 'faculty' and request.user.faculty_approved),
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
            complaint = form.save(commit=False)
            complaint.student = request.user
            complaint.assigned_unit = DEFAULT_ASSIGNMENT_UNIT.get(
                complaint.category, Complaint.AssignmentUnit.OTHER,
            )
            complaint.save()
            messages.success(request, f'Complaint submitted. Reference: {complaint.reference}')
            return redirect('complaint_detail', pk=complaint.pk)
    else: form = ComplaintForm()
    return render(request, 'complaints/complaint_form.html', {'form': form})

@login_required
def complaint_detail(request, pk):
    complaint = get_object_or_404(Complaint.objects.select_related('student','assigned_to').prefetch_related('updates__author'), pk=pk)
    faculty = request.user.role == 'faculty' and request.user.faculty_approved
    assigned_staff = request.user.role in ('maintenance', 'library') and complaint.assigned_to_id == request.user.id
    administrator = request.user.is_superuser or request.user.role == 'admin'
    hod = request.user.role == 'hod' and complaint.student.branch == request.user.branch
    allowed = administrator or hod or complaint.student_id == request.user.id or (faculty and complaint.assigned_to_id == request.user.id) or assigned_staff
    if not allowed: return render(request, '403.html', status=403)
    staff_access = administrator or hod or (faculty and complaint.assigned_to_id == request.user.id) or assigned_staff
    form = UpdateForm(initial={'status': complaint.status, 'resolution': complaint.resolution})
    assignment_form = ComplaintAssignmentForm(instance=complaint) if administrator else None
    if request.method == 'POST' and staff_access and administrator and request.POST.get('action') == 'assign':
        assignment_form = ComplaintAssignmentForm(request.POST, instance=complaint)
        if assignment_form.is_valid():
            assigned = assignment_form.save()
            target = (assigned.assigned_to.get_full_name() or assigned.assigned_to.email) if assigned.assigned_to else 'the unassigned queue'
            ComplaintUpdate.objects.create(complaint=complaint, author=request.user, message=f'Assignment updated: {assigned.get_assigned_unit_display()} → {target}.', visible_to_student=True)
            messages.success(request, 'Complaint assignment saved.')
            return redirect('complaint_detail', pk=pk)
    elif request.method == 'POST' and staff_access and request.POST.get('action') == 'update':
        form = UpdateForm(request.POST)
        if form.is_valid():
            ComplaintUpdate.objects.create(complaint=complaint, author=request.user, message=form.cleaned_data['message'], visible_to_student=form.cleaned_data['visible_to_student'])
            complaint.status = form.cleaned_data['status']
            complaint.resolution = form.cleaned_data['resolution']
            complaint.save(update_fields=['status','resolution','updated_at'])
            messages.success(request, 'Complaint status and update saved.')
            return redirect('complaint_detail', pk=pk)
    elif not (request.method == 'POST' and staff_access and request.POST.get('action') == 'update'):
        form = UpdateForm(initial={'status': complaint.status, 'resolution': complaint.resolution})
    updates = complaint.updates.all()
    if complaint.student_id == request.user.id: updates = updates.filter(visible_to_student=True)
    return render(request, 'complaints/complaint_detail.html', {'complaint': complaint, 'updates': updates, 'form': form, 'staff_access': staff_access, 'administrator': administrator, 'assignment_form': assignment_form})
