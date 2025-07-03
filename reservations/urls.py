from django.urls import path, include
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
    path('espaces/', views.liste_espaces, name='liste_espaces'),
    path('reserver/<int:espace_id>/', views.reserver_espace, name='reserver'),
    path('mes-reservations/', views.mes_reservations, name='mes_reservations'),
     path('reservations/annuler/<int:reservation_id>/', views.annuler_reservation, name='annuler_reservation'),
    path('evenement/<int:id>/', views.detail_evenement, name='detail_evenement'),
    path('evenement/<int:id>/avis/', views.ajouter_avis, name='ajouter_avis'),
    path('evenements/<int:evenement_id>/inscription/', views.inscription_evenement, name='inscription_evenement'),
    path('evenement/<int:inscription_id>/facture/', views.facture_evenement_pdf, name='facture_evenement_pdf'),
    path('paiement_evenement/<int:inscription_id>/success/', views.paiement_evenement_reussi, name='paiement_evenement_reussi'),
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
    #paypal
    path('paypal', include("paypal.standard.ipn.urls")),
    path('paiement-reussi/', views.paiement_reussi, name='paiement_reussi'),
    path('paiement-annule/', views.paiement_annule, name='paiement_annule'),
    path('payer/<int:reservation_id>/', views.payer_reservation, name='payer_reservation'),
    path('reservation-payee/<int:reservation_id>/', views.reservation_payee, name='reservation_payee'),
    
    path('facture/<int:reservation_id>/', views.generer_facture_pdf, name='generer_facture'),
]
