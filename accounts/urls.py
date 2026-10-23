from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import VerifiedAuthenticationForm
urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('verify-email/', views.verify_email, name='verify_email'),
    path('resend-code/', views.resend_code, name='resend_code'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html', authentication_form=VerifiedAuthenticationForm), name='login'),
    path('logout/', views.logout_view, name='logout'),
]
