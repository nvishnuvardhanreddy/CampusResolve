from django.contrib import admin
from django.urls import include, path
from django.http import JsonResponse
from django.db import DatabaseError, connection


def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
    except DatabaseError:
        return JsonResponse({'status': 'unavailable'}, status=503)
    return JsonResponse({'status': 'ok'})

urlpatterns = [
    path('healthz/', health_check, name='health_check'),
    path('admin/', admin.site.urls),
    path('', include('complaints.urls')),
    path('accounts/', include('accounts.urls')),
]
