from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Espace, Reservation, Evenement, Avis, Utilisateur,StatutEvenement
from .forms import ReservationForm, AvisForm, EspaceForm,EvenementForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from .forms import InscriptionForm
from .forms import ConnexionForm
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from .forms import ModifierProfilForm
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden
from django.contrib.admin.views.decorators import staff_member_required
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
import uuid
from django.http import HttpResponse
from django.conf import settings
from .models import InscriptionEvenement
from django.template.loader import get_template
from xhtml2pdf import pisa
from paypal.standard.forms import PayPalPaymentsForm
from django.template.loader import render_to_string 
def reserver_espace(request, espace_id):
    espace = get_object_or_404(Espace, id=espace_id)
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        print("Formulaire reçu :", form.data)
        if form.is_valid():
            print("Formulaire valide")
            reservation = form.save(commit=False)
            duree = (reservation.date_fin - reservation.date_debut).total_seconds() / 3600
            duree_decimal = Decimal(str(round(duree, 2)))
            prix_horaire = espace.tarif_par_heure
            total = duree_decimal * prix_horaire
            reservation.montant_total = total.quantize(Decimal('0.00'))
            reservation.membre = request.user
            reservation.espace = espace
            reservation.save()
            # Conversion MAD -> EUR (taux fixe ou dynamique)
            taux_conversion = Decimal('11')  # 11 MAD = 1 EUR (exemple)
            montant_en_eur = (reservation.montant_total / taux_conversion).quantize(Decimal('0.00'))
            # Créer les données PayPal avec la bonne devise
            paypal_dict = {
                'business': settings.PAYPAL_TEST_EMAIL,
                'amount': montant_en_eur,
                'item_name': f"Réservation espace {espace.nom}",
                'invoice': str(uuid.uuid4()),
                'currency_code': 'EUR',  # PayPal sandbox accepte EUR, pas MAD
                'notify_url': request.build_absolute_uri(reverse('paypal-ipn')),
                'return_url': request.build_absolute_uri(reverse('paiement_reussi')),
                'cancel_return': request.build_absolute_uri(reverse('paiement_annule')),
            }
            context = {
                'reservation': reservation,
                'montant_mad': reservation.montant_total,  # montant original en MAD
                'montant_eur': montant_en_eur,  # montant converti en EUR
                'paypal_dict': paypal_dict,
                'paypal_url': 'https://www.sandbox.paypal.com/cgi-bin/webscr',
                'paypal_email': settings.PAYPAL_TEST_EMAIL,
            }
            return render(request, 'paiement.html', context)
        else:
            print("Formulaire NON valide :", form.errors)
    else:
        form = ReservationForm()
    return render(request, 'membre/mes_reservations.html', {'form': form, 'espace': espace})
def accueil(request):
    espaces = Espace.objects.all()
    utilisateur = None
    if request.user.is_authenticated:
        utilisateur = request.user
    return render(request, 'accueil.html', {'espaces': espaces, 'utilisateur': utilisateur})

def register(request):
    if request.method == 'POST':
        form = InscriptionForm(request.POST, request.FILES)
        if form.is_valid():
            utilisateur = form.save(commit=False)
            utilisateur.motDePasseHash = make_password(form.cleaned_data['mot_de_passe'])
            utilisateur.dateInscription = timezone.now()
            utilisateur.save()
            return redirect('login')  # Redirige vers la page de connexion
        else:
            return render(request, 'registration/register.html', {'form': form})
    else:
        form = InscriptionForm()
        return render(request, 'registration/register.html', {'form': form})
    # ---------------------- VUES MEMBRE ----------------------
@login_required
def espace_detail(request, id):
    espace = get_object_or_404(Espace, pk=id)
    return render(request, 'membre/espace_detail.html', {'espace': espace})

@login_required
def reserver_espace(request, espace_id):
    espace = get_object_or_404(Espace, pk=espace_id)
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.espace = espace
            reservation.membre = request.user
            reservation.save()
            return redirect('mes_reservations')
    else:
        form = ReservationForm()
    return render(request, 'membre/reserver.html', {'form': form, 'espace': espace})

@login_required
def mes_reservations(request):
    reservations = Reservation.objects.filter(membre=request.user).select_related('espace').prefetch_related('services_utilises')
    
    # Recalculer les montants si nécessaire (optionnel)
    for res in reservations:
        if res.montant_total == Decimal('0.00'):
            res.calculer_montant_total()

        # Ajouter une propriété temporaire pour indiquer si la réservation est terminée
        res.terminee = res.date_fin < timezone.now()

    context = {
        'reservations': reservations,
        'total_general': sum(res.montant_total for res in reservations)
    }
    return render(request, 'membre/mes_reservations.html', context)

@login_required
def detail_evenement(request, id):
    evenement = get_object_or_404(Evenement, pk=id)
    return render(request, 'membre/detail_evenement.html', {'evenement': evenement})

@login_required
def profil_utilisateur(request):
    utilisateur = request.user
    return render(request, 'membre/profil.html', {'utilisateur': utilisateur})

@login_required
def ajouter_avis(request, espace_id):
    espace = get_object_or_404(Espace, pk=espace_id)
    if request.method == 'POST':
        form = AvisForm(request.POST)
        if form.is_valid():
            avis = form.save(commit=False)
            avis.membre = request.user
            avis.espace = espace
            avis.save()
            return redirect('espace_detail', id=espace.id)
    else:
        form = AvisForm()
    return render(request, 'membre/ajouter_avis.html', {'form': form, 'espace': espace})
def liste_utilisateurs(request):
    utilisateurs = Utilisateur.objects.all()
    return render(request, 'admin/utilisateurs.html', {'utilisateurs': utilisateurs})

@login_required
def liste_espaces(request):
    espaces = Espace.objects.all()
    return render(request, 'membre/liste_espaces.html', {'espaces': espaces})
# ---------------------- VUES ADMIN ----------------------
def est_admin(user):
    return user.is_authenticated and user.role == 'admin'

@login_required
@user_passes_test(est_admin)
def admin_ajouter_espace(request):
    if request.method == 'POST':
        form = EspaceForm(request.POST, request.FILES)  # <-- Ajoute request.FILES ici
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
    else:
        form = EspaceForm()
    return render(request, 'admin/ajouter_espace.html', {'form': form})

@login_required
@user_passes_test(est_admin)
def admin_modifier_espace(request, id):
    espace = get_object_or_404(Espace, pk=id)
    if request.method == 'POST':
        form = EspaceForm(request.POST, request.FILES, instance=espace)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
    else:
        form = EspaceForm(instance=espace)
    return render(request, 'admin/modifier_espace.html', {'form': form, 'espace': espace})
@login_required
@user_passes_test(est_admin)
def profil_admin(request):
    utilisateur = request.user
    return render(request, 'admin/profile_admin.html', {'utilisateur': utilisateur})
@login_required
@user_passes_test(est_admin)
def admin_reservations(request):
    reservations = Reservation.objects.select_related('membre', 'espace').all()
    return render(request, 'admin/reservations.html', {'reservations': reservations})

@login_required
@user_passes_test(est_admin)
def admin_utilisateurs(request):
    utilisateurs = Utilisateur.objects.all()
    return render(request, 'admin/utilisateurs.html', {'utilisateurs': utilisateurs})
@login_required
def modifier_profil_admin(request):
    utilisateur = request.user
    if request.method == 'POST':
        utilisateur.first_name = request.POST.get('first_name')
        utilisateur.last_name = request.POST.get('last_name')
        utilisateur.email = request.POST.get('email')

        if 'photoProfil' in request.FILES:
            utilisateur.photoProfil = request.FILES['photoProfil']

        utilisateur.save()
        messages.success(request, "Profil modifié avec succès.")
        return redirect('profil_admin')

    return render(request, 'admin/modifier_profil_admin.html', {'utilisateur': utilisateur})
@login_required
@user_passes_test(est_admin)
def modifier_role_utilisateur(request, user_id):
    utilisateur = get_object_or_404(Utilisateur, id=user_id)
    if request.method == 'POST':
        nouveau_role = request.POST.get('role')
        if nouveau_role in ['admin', 'membre']:
            utilisateur.role = nouveau_role
            utilisateur.save()
        return redirect('admin_utilisateurs')  # redirige vers ta liste

    return render(request, 'admin/modifier_role.html', {'utilisateur': utilisateur})
@login_required
@user_passes_test(est_admin)
def supprimer_utilisateur(request, user_id):
    utilisateur = get_object_or_404(Utilisateur, id=user_id)
    if request.method == 'POST':
        utilisateur.delete()
        return redirect('admin_utilisateurs')

    return render(request, 'admin/confirmation_suppression.html', {'utilisateur': utilisateur})

@login_required
@user_passes_test(est_admin)
def admin_evenements(request):
    evenements = Evenement.objects.all()
    return render(request, 'admin/evenements.html', {'evenements': evenements})

@login_required(login_url='login')  # redirige vers login si pas connecté
@user_passes_test(est_admin, login_url='login')  # redirige vers login si pas admin
def admin_dashboard(request):
    # ta logique
    total_espaces = Espace.objects.count()
    total_reservations = Reservation.objects.count()
    total_utilisateurs = Utilisateur.objects.count()
    total_evenements = Evenement.objects.count()
    return render(request, 'admin/dashboard.html', {
        'total_espaces': total_espaces,
        'total_reservations': total_reservations,
        'total_utilisateurs': total_utilisateurs,
        'total_evenements': total_evenements,
    })

def login_view(request):
    if request.method == 'POST':
        form = ConnexionForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            mot_de_passe = form.cleaned_data['mot_de_passe']

            # Authentification
            utilisateur = authenticate(request, username=email, password=mot_de_passe)

            if utilisateur is not None:
                login(request, utilisateur)

                # Redirection selon le rôle
                if utilisateur.role == 'admin':
                    return redirect('admin_dashboard')
                else:
                    return redirect('accueil')
            else:
                form.add_error(None, "Email ou mot de passe incorrect.")
    else:
        form = ConnexionForm()

    return render(request, 'registration/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def profil(request):
    return render(request, 'membre/profil.html', {'utilisateur': request.user})

@login_required
def modifier_profil(request):
    utilisateur = request.user
    if request.method == 'POST':
        form = ModifierProfilForm(request.POST, request.FILES, instance=utilisateur)
        if form.is_valid():
            form.save()
            return redirect('profil')  # nom de l’URL du profil
    else:
        form = ModifierProfilForm(instance=utilisateur)

    return render(request, 'membre/modifier_profile.html', {'form': form})
@login_required
def ajouter_evenement(request):
    if request.method == 'POST':
        form = EvenementForm(request.POST)
        if form.is_valid():
            evenement = form.save(commit=False)
            utilisateur = request.user
            evenement.organisateur = utilisateur

            if utilisateur.est_admin():
                evenement.statut = 'valide'
            else:
                evenement.statut = 'attente'

            evenement.save()
            return redirect('liste_evenements')  # adapte à ton URL
    else:
        form = EvenementForm()
    
    return render(request, 'evenements/ajouter_evenement.html', {'form': form})
@login_required
def liste_evenements(request):
    utilisateur = request.user
    if utilisateur.est_admin():
        # Admin voit tous les événements
        evenements = Evenement.objects.all().order_by('-date_debut')
    else:
        # Membre voit uniquement les événements validés
        evenements = Evenement.objects.filter(statut='valide').order_by('-date_debut')
    return render(request, 'evenements/liste_evenements.html', {'evenements': evenements})

@login_required
def inscription_evenement(request, evenement_id):
    evenement = get_object_or_404(Evenement, id=evenement_id)

    # Vérifie si déjà inscrit (optionnel)
    deja_inscrit = InscriptionEvenement.objects.filter(evenement=evenement, utilisateur=request.user).exists()
    # if deja_inscrit:
    #     messages.info(request, "Déjà inscrit")
    #     return redirect('detail_evenement', evenement_id)

    # Crée l'inscription
    inscription = InscriptionEvenement.objects.create(evenement=evenement, utilisateur=request.user)

    # Génère une facture
    facture_id = str(uuid.uuid4())

    # Convertir le prix MAD -> EUR
    taux_conversion = Decimal('11')  # 11 MAD = 1 EUR (exemple)
    montant_eur = (Decimal(evenement.prix) / taux_conversion).quantize(Decimal('0.00'))

    paypal_dict = {
        'business': settings.PAYPAL_TEST_EMAIL,
        'amount': montant_eur,
        'item_name': f"Inscription événement {evenement.titre}",
        'invoice': facture_id,
        'currency_code': 'EUR',
        'notify_url': request.build_absolute_uri(reverse('paypal-ipn')),
        'return_url': request.build_absolute_uri(reverse('paiement_evenement_reussi', args=[inscription.id])),
        'cancel_return': request.build_absolute_uri(reverse('liste_evenements')),
    }

    context = {
        'evenement': evenement,
        'inscription': inscription,
        'facture_id': facture_id,
        'paypal_url': 'https://www.sandbox.paypal.com/cgi-bin/webscr',
        'paypal_email': settings.PAYPAL_TEST_EMAIL,
        'montant_mad': evenement.prix,
        'montant_eur': montant_eur,
        'paypal_dict': paypal_dict,
    }

    return render(request, 'evenements/inscription_paiement.html', context)
@user_passes_test(lambda u: u.is_authenticated and u.est_admin())
def valider_evenement(request, evenement_id):
    evenement = get_object_or_404(Evenement, id=evenement_id)
    evenement.statut = 'valide'
    evenement.save()
    return redirect('liste_evenements') 
@login_required
@user_passes_test(lambda u: u.is_authenticated and u.est_admin())
def admin_evenements(request):
    evenements = Evenement.objects.all().order_by('-date_debut')
    return render(request, 'admin/evenements.html', {'evenements': evenements})
def evenement_detail(request, evenement_id):
    evenement = get_object_or_404(Evenement, pk=evenement_id)
    return render(request, 'evenement_detail.html', {'evenement': evenement})
@require_POST
def supprimer_evenement(request, evenement_id):
    evenement = get_object_or_404(Evenement, pk=evenement_id)
    evenement.delete()
    messages.success(request, "Événement supprimé avec succès.")
    return redirect('liste_evenements')
@staff_member_required
def voir_inscrits(request, evenement_id):
    evenement = get_object_or_404(Evenement, id=evenement_id)
    inscrits = evenement.participants.all()

    return render(request, 'admin/voir_inscrits.html', {
        'evenement': evenement,
        'inscrits': inscrits
    })
@staff_member_required
def admin_voir_reservations(request):
    reservations = Reservation.objects.select_related('utilisateur', 'espace').all().order_by('-date_debut')
    return render(request, 'admin/reservations.html', {'reservations': reservations})
def paiement_reussi(request):
    return HttpResponse(" Paiement réussi. Merci pour votre réservation.")

def paiement_annule(request):
    return HttpResponse(" Paiement annulé. Vous pouvez réessayer.")

def payer_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, membre=request.user)

    # Convertir MAD en EUR (si nécessaire)
    taux_conversion = Decimal('11')  # 11 MAD = 1 EUR
    montant_en_eur = (reservation.montant_total / taux_conversion).quantize(Decimal('0.00'))

    paypal_dict = {
        'business': settings.PAYPAL_TEST_EMAIL,
        'amount': montant_en_eur,
        'item_name': f"Réservation espace {reservation.espace.nom}",
        'invoice': str(reservation.id),
        'currency_code': 'EUR',
        'notify_url': request.build_absolute_uri(reverse('paypal-ipn')),
        'return_url': request.build_absolute_uri(reverse('reservation_payee', args=[reservation.id])),
        'cancel_return': request.build_absolute_uri(reverse('mes_reservations')),
    }

    form = PayPalPaymentsForm(initial=paypal_dict)

    return render(request, 'paiement.html', {
        'reservation': reservation,
        'form': form,
        'montant_mad': reservation.montant_total,
        'montant_eur': montant_en_eur,
        'paypal_url': settings.PAYPAL_URL,  # défini dans settings.py
        'paypal_email': settings.PAYPAL_TEST_EMAIL,
    })
def reservation_payee(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, membre=request.user)
    reservation.status = "payé" 
    return render(request, 'confirmation_paiement.html', {'reservation': reservation})

@login_required
def paiement_evenement_reussi(request, inscription_id):
    inscription = get_object_or_404(InscriptionEvenement, id=inscription_id, utilisateur=request.user)

    if not inscription.paiement_effectue:
        inscription.paiement_effectue = True
        inscription.save()

    return render(request, 'evenements/paiement_reussi.html', {
        'inscription': inscription
    })
def generer_facture_pdf(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)

    template = get_template('facture.html')
    html = template.render({'reservation': reservation})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="facture_{reservation.id}.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Erreur lors de la génération du PDF')
    return response
def retour_paypal(request):
    reservation_id = request.GET.get('reservation_id')
    
    if not reservation_id:
        messages.error(request, "Aucune réservation spécifiée.")
        return redirect('home')  # Rediriger vers la page d'accueil ou une autre page

    reservation = get_object_or_404(Reservation, id=reservation_id)

    # Marquer la réservation comme payée (si ton modèle a ce champ)
    if not reservation.is_paid:
        reservation.is_paid = True
        reservation.save()

    messages.success(request, "Le paiement a été effectué avec succès.")

    return render(request, 'confirmation_paiement.html', {
        'reservation': reservation
    })

@login_required
def annuler_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)

    # Vérifie que c'est bien le propriétaire
    if reservation.membre != request.user:
        return HttpResponseForbidden("Vous n'avez pas la permission d'annuler cette réservation.")

    # On vérifie que la réservation est à venir (pas terminée)
    if reservation.terminee:
        # Optionnel : message d'erreur, ou redirection
        return redirect('mes_reservations')  # ou une autre page

    if request.method == 'POST':
        reservation.delete()
        # Optionnel : message de succès avec messages framework
        return redirect('mes_reservations')

    # Pour gérer le cas GET (ex: confirmation), on peut rediriger
    return redirect('mes_reservations')

@login_required
def facture_evenement_pdf(request, inscription_id):
    inscription = get_object_or_404(InscriptionEvenement, id=inscription_id, utilisateur=request.user)

    if not inscription.paiement_effectue:
        return HttpResponse("Paiement non effectué", status=403)

    # Rendu HTML du template
    html = render_to_string('evenements/facture_evenement.html', {
        'inscription': inscription,
        'evenement': inscription.evenement,
        'utilisateur': request.user,
        'montant': inscription.evenement.prix,
    })

    # Préparation de la réponse HTTP
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="facture_evenement_{inscription.id}.pdf"'

    # Génération du PDF avec pisa
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse("Une erreur est survenue lors de la génération du PDF", status=500)

    return response