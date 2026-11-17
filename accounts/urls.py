from django.urls import path, reverse_lazy
from django.conf import settings
from django.contrib.auth import views as auth_views
from . import views
from .forms import VerifiedAuthenticationForm
urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('verify-email/', views.verify_email, name='verify_email'),
    path('resend-code/', views.resend_code, name='resend_code'),
    path('demo-login/', views.demo_login, name='demo_login'),
    path('profile/', views.profile, name='profile'),
    path('password-change/', auth_views.PasswordChangeView.as_view(
        template_name='accounts/password_change.html',
        success_url=reverse_lazy('profile'),
    ), name='password_change'),
    path('login/', auth_views.LoginView.as_view(
        template_name='accounts/login.html',
        authentication_form=VerifiedAuthenticationForm,
        extra_context={'show_demo_accounts': settings.DEBUG},
    ), name='login'),
    path('logout/', views.logout_view, name='logout'),
]
