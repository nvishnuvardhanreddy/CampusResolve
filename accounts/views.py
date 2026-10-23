import secrets
from datetime import timedelta
from smtplib import SMTPException
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from .forms import SignUpForm
from .models import EmailOTP

def send_code(user):
    now = timezone.now()
    latest = user.email_otps.order_by('-created_at').first()
    if latest and (now - latest.created_at).total_seconds() < settings.OTP_RESEND_SECONDS:
        return False
    raw = f'{secrets.randbelow(1_000_000):06d}'
    otp = EmailOTP.objects.create(user=user, code_digest=make_password(raw), expires_at=now + timedelta(minutes=settings.OTP_TTL_MINUTES))
    try:
        send_mail('Your CampusResolve verification code', f'Your verification code is {raw}. It expires in {settings.OTP_TTL_MINUTES} minutes. If you did not request this, ignore this email.', settings.DEFAULT_FROM_EMAIL, [user.email])
    except (SMTPException, OSError, RuntimeError):
        otp.delete()
        raise
    return True

def signup(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = SignUpForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        request.session['pending_verification_user'] = user.pk
        try:
            send_code(user)
            messages.success(request, 'We sent a six-digit verification code to your email address.')
        except (SMTPException, OSError, RuntimeError):
            messages.error(request, 'We could not send the verification email. Check the email settings and try sending a new code.')
        return redirect('verify_email')
    return render(request, 'accounts/signup.html', {'form': form})

def verify_email(request):
    user_id = request.session.get('pending_verification_user')
    from .models import User
    user = User.objects.filter(pk=user_id, email_verified=False).first()
    if not user:
        messages.info(request, 'Create an account to begin email verification.')
        return redirect('signup')
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        otp = user.email_otps.filter(consumed_at__isnull=True).order_by('-created_at').first()
        if not otp or otp.expires_at <= timezone.now() or otp.attempts >= 5:
            messages.error(request, 'That code has expired or reached its attempt limit. Request a new code.')
        else:
            otp.attempts += 1
            otp.save(update_fields=['attempts'])
            if check_password(code, otp.code_digest):
                otp.consumed_at = timezone.now()
                otp.save(update_fields=['consumed_at'])
                user.email_verified = True
                user.save(update_fields=['email_verified'])
                request.session.pop('pending_verification_user', None)
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, 'Your email is verified. Welcome to Campus Resolve.')
                return redirect('dashboard')
            messages.error(request, 'The code is incorrect. Please try again.')
    return render(request, 'accounts/verify_email.html', {'email': user.email})

@require_POST
def resend_code(request):
    from .models import User
    user = User.objects.filter(pk=request.session.get('pending_verification_user'), email_verified=False).first()
    if user:
        try:
            if send_code(user): messages.success(request, 'A new code has been sent.')
            else: messages.warning(request, 'Please wait a minute before requesting another code.')
        except (SMTPException, OSError, RuntimeError):
            messages.error(request, 'We could not send the email. Check SMTP settings and try again shortly.')
        return redirect('verify_email')
    return redirect('signup')

@login_required
def logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('home')
