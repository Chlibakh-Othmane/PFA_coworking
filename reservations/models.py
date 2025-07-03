from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid
from django.contrib.auth.models import AbstractUser
from decimal import Decimal 
from django.conf import settings

class Disponibilite(models.Model):
    date = models.DateField()
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()

    def _str_(self):
        return f"{self.date} ({self.heure_debut} - {self.heure_fin})"
class Avis(models.Model):
    membre = models.ForeignKey('Utilisateur', on_delete=models.CASCADE, limit_choices_to={'role': 'membre'})
    espace = models.ForeignKey('Espace', on_delete=models.CASCADE, related_name='avis')
    note = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # note de 1 à 5
    commentaire = models.TextField(blank=True)
    date_creation = models.DateTimeField(default=timezone.now)

    def _str_(self):
        return f"Avis de {self.membre.username} sur {self.espace.nom} - {self.note}/5"

class Espace(models.Model):
    nom = models.CharField(max_length=100)
    capacite = models.IntegerField()
    equipements = models.TextField(help_text="Liste des équipements, séparés par des virgules")
    tarif_par_heure = models.DecimalField(max_digits=10, decimal_places=2)
    disponibilites = models.ManyToManyField('Disponibilite', related_name='espaces')
    image = models.ImageField(upload_to='espaces/', blank=True, null=True)
    note_moyenne = models.FloatField(default=0.0)
    nombre_avis = models.IntegerField(default=0)

    def _str_(self):
        return self.nom

    def est_disponible(self, date_debut, date_fin):
        reservations = self.reservation_set.filter(
            date_debut__lt=date_fin,
            date_fin__gt=date_debut,
            statut='approuvee'
        )
        return not reservations.exists()

    def calculer_montant_total(self, date_debut, date_fin):
        delta = date_fin - date_debut
        heures = delta.total_seconds() / 3600
        return round(self.tarif_par_heure * heures, 2)

    def moyenne_avis(self):
        avis = self.avis_set.all()
        if avis.exists():
            total = sum(a.note for a in avis)
            return round(total / avis.count(), 1)
        return 0

    def est_recommande(self):
        return self.moyenne_avis() >= 4.0

class StatutReservation(models.TextChoices):
    EN_ATTENTE = 'en_attente', 'En attente'
    CONFIRMEE = 'confirmee', 'Confirmée'
    ANNULEE = 'annulee', 'Annulée'
    TERMINEE = 'terminee', 'Terminée'
    APPROUVEE = 'approuvee', 'Approuvée'

class Service(models.Model):  # N'EST PLUS ABSTRAITE
    nom = models.CharField(max_length=100)
    est_gratuit = models.BooleanField(default=False)
    prix = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)

    def est_payant(self):
        return not self.est_gratuit

    def get_prix_affiche(self):
        return "Gratuit" if self.est_gratuit else f"{self.prix} DH"

class ServiceMateriel(Service):
    quantite_disponible = models.PositiveIntegerField(default=1)
    garantie = models.BooleanField(default=False)
    marque = models.CharField(max_length=100, blank=True)

    def est_disponible(self):
        return self.quantite_disponible > 0

class ServiceRestauration(Service):
    TYPE_REPAS_CHOICES = [
        ('petit_dej', 'Petit Déjeuner'),
        ('dej', 'Déjeuner'),
        ('diner', 'Dîner'),
        ('snack', 'Snack'),
        ('boisson', 'Boisson'),
    ]
    type_repas = models.CharField(max_length=20, choices=TYPE_REPAS_CHOICES)

    def _str_(self):
        return f"{self.nom} ({self.get_type_repas_display()})"

class Utilisateur(AbstractUser):
    class Role(models.TextChoices):
        MEMBRE = 'membre', 'Membre'
        ADMIN = 'admin', 'Administrateur'

    # CHAMPS SUPPLÉMENTAIRES UNIQUEMENT
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.MEMBRE)
    photoProfil = models.ImageField(upload_to="photos/", blank=True, null=True)
    dateInscription = models.DateTimeField(default=timezone.now)
    tentativesConnexion = models.IntegerField(default=0)
    estBloque = models.BooleanField(default=False)
    email = models.EmailField(unique=True)

    # On change le champ d'identifiant
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    def est_admin(self):
        return self.role == self.Role.ADMIN

    def reinitialiserMotDePasse(self, nouveau_mot_de_passe):
        self.set_password(nouveau_mot_de_passe)
        self.save()

    def ajouterPhotoProfil(self, photo):
        self.photoProfil = photo
        self.save()

    def supprimerPhotoProfil(self):
        if self.photoProfil:
            self.photoProfil.delete(save=False)
        self.photoProfil = None
        self.save()

    def recevoirNotification(self, message, notification_type="info", request=None):
        print(f"[Notification {notification_type.upper()}] pour {self.email}: {message}")
        if request:
            from django.contrib import messages
            niveau = {
                "info": messages.INFO,
                "success": messages.SUCCESS,
                "warning": messages.WARNING,
                "error": messages.ERROR
            }.get(notification_type, messages.INFO)
            messages.add_message(request, niveau, f"Notification: {message}")

    def _str_(self):
        return self.get_full_name() or self.username

class Reservation(models.Model):
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    statut = models.CharField(max_length=20, choices=StatutReservation.choices, default=StatutReservation.EN_ATTENTE)
    montant_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    qr_code = models.CharField(max_length=255, blank=True)
    reduction_pourcent = models.FloatField(default=0.0)
    services_utilises = models.ManyToManyField(Service, blank=True)
    membre = models.ForeignKey('Utilisateur', on_delete=models.CASCADE, limit_choices_to={'role': 'membre'})
    espace = models.ForeignKey(Espace, on_delete=models.CASCADE)
    payee = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=False)
    def _str_(self):
        return f"Réservation #{self.id} - {self.espace.nom}"
    def duree(self):
        duree_sec = (self.date_fin - self.date_debut).total_seconds()
        duree_heure = duree_sec / 3600
        return round(duree_heure, 2)
    def appliquer_reduction(self):
        self.montant_total *= (1 - self.reduction_pourcent / 100)
        self.save()

    def calculer_montant(self):
        duree_heures = Decimal((self.date_fin - self.date_debut).total_seconds()) / Decimal(3600)
        self.montant_total = Decimal(self.espace.tarif_par_heure) * duree_heures.quantize(Decimal('0.01'))
        self.save()
        return self.montant_total

    def calculer_montant_total(self):
        """Calcule le montant total avec services"""
        montant = self.calculer_montant()  # Montant de base
        
        # Ajout des services en conservant le type Decimal
        for service in self.services_utilises.all():
            if service.est_payant():
                montant += Decimal(str(service.prix))  # Conversion propre en Decimal
        
        self.montant_total = montant.quantize(Decimal('0.00'))
        self.save()
        return self.montant_total

    @property
    def duree_heures(self):
        """Propriété pour afficher la durée en heures dans le template"""
        delta = self.date_fin - self.date_debut
        return round(delta.total_seconds() / 3600, 2)

    def annuler(self):
        self.statut = StatutReservation.ANNULEE
        self.save()

    def modifier(self, nouvelle_date_debut, nouvelle_date_fin):
        self.date_debut = nouvelle_date_debut
        self.date_fin = nouvelle_date_fin
        self.calculer_montant()
        self.save()

    def generer_qr_code(self):
        self.qr_code = f"QR-{uuid.uuid4().hex[:10]}"
        self.save()

class StatutEvenement(models.TextChoices):
    EN_ATTENTE = 'en_attente', 'En attente'
    VALIDE = 'valide', 'Validé'
    ANNULE = 'annule', 'Annulé'

class Evenement(models.Model):
    titre = models.CharField(max_length=100)
    description = models.TextField()
    categorie = models.CharField(max_length=50)
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    statut = models.CharField(max_length=20, choices=StatutEvenement.choices, default=StatutEvenement.EN_ATTENTE)
    capacite_max = models.PositiveIntegerField(default=20)
    organisateur = models.ForeignKey('Utilisateur', on_delete=models.CASCADE)
    reservations = models.ManyToManyField(Reservation, blank=True)
    participants = models.ManyToManyField('Utilisateur', blank=True, related_name="evenements_participes")
    services = models.CharField(max_length=255, blank=True, help_text="Liste des services séparés par des virgules")
    prix = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    def _str_(self):
        return self.titre

    def est_actif(self):
        maintenant = timezone.now()
        return self.date_debut <= maintenant <= self.date_fin

    def valider(self):
        self.statut = StatutEvenement.VALIDE
        self.save()

    def annuler(self):
        self.statut = StatutEvenement.ANNULE
        self.save()

    def est_complet(self):
        return self.participants.count() >= self.capacite_max

    def inscrire_utilisateur(self, utilisateur):
        if not self.est_complet():
            self.participants.add(utilisateur)
            return True
        return False

    def desinscrire_utilisateur(self, utilisateur):
        if self.participants.filter(id=utilisateur.id).exists():
            self.participants.remove(utilisateur)
            return True
        return False
class InscriptionEvenement(models.Model):
    evenement = models.ForeignKey('Evenement', on_delete=models.CASCADE)
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date_inscription = models.DateTimeField(auto_now_add=True)
    paiement_effectue = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.utilisateur.username} -> {self.evenement.titre}"