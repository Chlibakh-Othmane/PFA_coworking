from django.contrib import admin
from .models import (
    Disponibilite,
    Espace,
    Reservation,
    Service,
    ServiceMateriel,
    ServiceRestauration,
    Utilisateur,
    Evenement
)

@admin.register(Espace)
class EspaceAdmin(admin.ModelAdmin):
    list_display = ("nom", "capacite", "tarif_par_heure")
    search_fields = ("nom",)
    list_filter = ("capacite",)

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("id", "espace", "membre", "date_debut", "date_fin", "statut")
    list_filter = ("statut", "date_debut")
    search_fields = ("espace__nom", "membre__nom")

@admin.register(Disponibilite)
class DisponibiliteAdmin(admin.ModelAdmin):
    list_display = ("date", "heure_debut", "heure_fin")

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("nom", "est_gratuit", "prix")
    list_filter = ("est_gratuit",)

@admin.register(ServiceMateriel)
class ServiceMaterielAdmin(admin.ModelAdmin):
    list_display = ("nom", "marque", "quantite_disponible", "garantie")

@admin.register(ServiceRestauration)
class ServiceRestaurationAdmin(admin.ModelAdmin):
    list_display = ("nom", "type_repas", "est_gratuit", "prix")

@admin.register(Utilisateur)
class UtilisateurAdmin(admin.ModelAdmin):
    list_display = ("first_name", "email", "role", "estBloque", "dateInscription")
    list_filter = ("role", "estBloque")
    search_fields = ("nom", "email")

@admin.register(Evenement)
class EvenementAdmin(admin.ModelAdmin):
    list_display = ("titre", "categorie", "date_debut", "date_fin", "statut")
    list_filter = ("statut", "categorie")
    search_fields = ("titre", "description")
