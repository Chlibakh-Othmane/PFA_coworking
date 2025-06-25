from django.contrib.auth import views as auth_views
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from reservations import views

urlpatterns = [
    path('', include('reservations.urls')),
    path('login/', views.login_view, name='login'),  # <- celui qu'on va utiliser
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/utilisateurs/', views.admin_utilisateurs, name='admin_utilisateurs'),
    path('utilisateurs/<int:user_id>/modifier-role/', views.modifier_role_utilisateur, name='modifier_role_utilisateur'),
    path('admin/utilisateurs/<int:user_id>/supprimer/', views.supprimer_utilisateur, name='supprimer_utilisateur'),
    path('admin/', admin.site.urls),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)