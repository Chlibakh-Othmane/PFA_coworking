from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid

class Disponibilite(models.Model):
    date = models.DateField()
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()

    def __str__(self):
        return f"{self.date} ({self.heure_debut} - {self.heure_fin})"

class Espace(models.Model):
    nom = models.CharField(max_length=100)
    capacite = models.IntegerField()
    equipements = models.TextField(help_text="Liste des équipements, séparés par des virgules")
    tarif_par_heure = models.DecimalField(max_digits=10, decimal_places=2)
    disponibilites = models.ManyToManyField('Disponibilite', related_name='espaces')

    def __str__(self):
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

    def __str__(self):
        return f"{self.nom} ({self.get_type_repas_display()})"

class Utilisateur(models.Model):
    nom = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    motDePasseHash = models.CharField(max_length=255)
    photoProfil = models.ImageField(upload_to="photos/", blank=True, null=True)
    dateInscription = models.DateTimeField(default=timezone.now)
    tentativesConnexion = models.IntegerField(default=0)
    estBloque = models.BooleanField(default=False)

    def authentifier(self, mot_de_passe):
        return check_password(mot_de_passe, self.motDePasseHash)

    def reinitialiserMotDePasse(self, nouveau_mot_de_passe):
        self.motDePasseHash = make_password(nouveau_mot_de_passe)
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

    def __str__(self):
        return self.nom

class Membre(Utilisateur):
    pass  # à compléter selon ton projet

class Reservation(models.Model):
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    statut = models.CharField(max_length=20, choices=StatutReservation.choices, default=StatutReservation.EN_ATTENTE)
    montant_total = models.FloatField(default=0.0)
    qr_code = models.CharField(max_length=255, blank=True)
    reduction_pourcent = models.FloatField(default=0.0)
    services_utilises = models.ManyToManyField(Service, blank=True)
    membre = models.ForeignKey(Membre, on_delete=models.CASCADE)
    espace = models.ForeignKey(Espace, on_delete=models.CASCADE)

    def __str__(self):
        return f"Réservation #{self.id} - {self.espace.nom}"

    def appliquer_reduction(self):
        self.montant_total *= (1 - self.reduction_pourcent / 100)
        self.save()

    def calculer_montant(self):
        duree_heures = (self.date_fin - self.date_debut).total_seconds() / 3600
        self.montant_total = round(self.espace.tarif_par_heure * duree_heures, 2)
        self.save()
        return self.montant_total

    def calculer_montant_total(self):
        montant = self.calculer_montant()
        for service in self.services_utilises.all():
            if service.est_payant():
                montant += float(service.prix)
        self.montant_total = montant
        self.save()
        return montant

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
    organisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    reservations = models.ManyToManyField(Reservation, blank=True)
    participants = models.ManyToManyField(Utilisateur, blank=True, related_name="evenements_participes")
    services = models.ManyToManyField(Service, blank=True, related_name="espaces")

    def __str__(self):
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

class Administrateur(Utilisateur):
    role = models.CharField(max_length=50, default="Administrateur")

    def ajouter_espace(self, nom, capacite, equipements, tarif_par_heure):
        return Espace.objects.create(
            nom=nom,
            capacite=capacite,
            equipements=equipements,
            tarif_par_heure=tarif_par_heure
        )

    def supprimer_espace(self, espace_id):
        try:
            espace = Espace.objects.get(id=espace_id)
            espace.delete()
            return True
        except Espace.DoesNotExist:
            return False

    def modifier_espace(self, espace_id, **kwargs):
        try:
            espace = Espace.objects.get(id=espace_id)
            for attr, value in kwargs.items():
                setattr(espace, attr, value)
            espace.save()
            return True
        except Espace.DoesNotExist:
            return False

    def reservations_a_venir(self):
        now = timezone.now()
        return Reservation.objects.filter(date_debut__gte=now, statut=StatutReservation.EN_ATTENTE)

    def approuver_reservation(self, reservation_id):
        try:
            reservation = Reservation.objects.get(id=reservation_id)
            reservation.statut = StatutReservation.APPROUVEE
            reservation.save()
            return True
        except Reservation.DoesNotExist:
            return False

    def annuler_reservation(self, reservation_id):
        try:
            reservation = Reservation.objects.get(id=reservation_id)
            reservation.statut = StatutReservation.ANNULEE
            reservation.save()
            return True
        except Reservation.DoesNotExist:
            return False

    def modifier_reservation(self, reservation_id, **kwargs):
        try:
            reservation = Reservation.objects.get(id=reservation_id)
            for attr, value in kwargs.items():
                setattr(reservation, attr, value)
            reservation.save()
            return True
        except Reservation.DoesNotExist:
            return False

    def reservations_passees(self):
        now = timezone.now()
        return Reservation.objects.filter(date_fin__lt=now)

    def attribuer_abonnement(self, membre_id, nom_abonnement, date_debut, date_fin):
        # À remplacer par ta classe Abonnement si elle existe
        print(f"Attribution de l'abonnement '{nom_abonnement}' à l'utilisateur {membre_id}")
        return True
