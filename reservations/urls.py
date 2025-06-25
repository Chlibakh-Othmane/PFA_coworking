from django.urls import path
from . import views

urlpatterns = [
    # Vues générales
    path('', views.accueil, name='accueil'),
    path('evenements/ajouter/', views.ajouter_evenement, name='ajouter_evenement'), 

     # Authentification
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('profil/modifier/', views.modifier_profil, name='modifier_profil'),

    # Membre
     path('profil/', views.profil, name='profil'),
    path('espace/<int:id>/', views.espace_detail, name='espace_detail'),
    path('reserver/<int:espace_id>/', views.reserver_espace, name='reserver'),
    path('mes-reservations/', views.mes_reservations, name='mes_reservations'),
    path('evenement/<int:id>/', views.detail_evenement, name='detail_evenement'),
    path('evenement/<int:id>/avis/', views.ajouter_avis, name='ajouter_avis'),
    path('evenements/<int:evenement_id>/inscription/', views.inscription_evenement, name='inscription_evenement'),
    


    # Admin
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/ajouter-espace/', views.admin_ajouter_espace, name='ajouter_espace'),
    path('admin/modifier-espace/<int:id>/', views.admin_modifier_espace, name='modifier_espace'),
    path('admin/reservations/', views.admin_reservations, name='admin_reservations'),
    path('admin/utilisateurs/', views.admin_utilisateurs, name='admin_utilisateurs'),
    path('admin/evenements/', views.admin_evenements, name='admin_evenements'),
    path('evenements/', views.liste_evenements, name='liste_evenements'),
    path('evenements/<int:evenement_id>/valider/', views.valider_evenement, name='valider_evenement'),
    path('evenement/<int:evenement_id>/supprimer/', views.supprimer_evenement, name='supprimer_evenement'),
    path('admin/evenement/<int:evenement_id>/inscrits/', views.voir_inscrits, name='voir_inscrits'),
    path('admin/profil/', views.profil_admin, name='profil_admin'),
    path('admin/profil/modifier/', views.modifier_profil_admin, name='modifier_profil_admin'),
    

]
