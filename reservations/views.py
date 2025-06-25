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
from django.contrib.admin.views.decorators import staff_member_required
from decimal import Decimal
def reserver_espace(request, espace_id):
    espace = get_object_or_404(Espace, id=espace_id)
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        print("Formulaire reçu :", form.data)
        if form.is_valid():
            print("Formulaire valide")
            reservation = form.save(commit=False)
            duree = (reservation.date_fin - reservation.date_debut).total_seconds() / 3600
            duree_decimal = Decimal(str(round(duree, 2)))  # conversion en Decimal
            prix_horaire = espace.tarif_par_heure  
            total = duree_decimal * prix_horaire
            reservation.montant_total = float(total) 
            reservation.membre = request.user
            reservation.espace = espace
            print("Durée:", duree_decimal)
            print("Prix horaire:", prix_horaire)
            print("Total calculé:", total)
            print("Montant avant save:", reservation.montant_total)

            reservation.save()
            return redirect('confirmation_reservation')
    else:
        print("Formulaire NON valide :", form.errors)
        form = ReservationForm()
        
    return render(request, 'membre/reserver.html', {'form': form, 'espace': espace})
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
    reservations = Reservation.objects.filter(membre=request.user)
    return render(request, 'membre/mes_reservations.html', {'reservations': reservations})

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

    if evenement.est_complet():
        messages.error(request, "Cet événement est complet.")
    elif evenement.statut != StatutEvenement.VALIDE:
        messages.warning(request, "Cet événement n’est pas disponible.")
    else:
        if evenement.participants.filter(id=request.user.id).exists():
            messages.info(request, "Vous êtes déjà inscrit.")
        else:
            evenement.inscrire_utilisateur(request.user)
            messages.success(request, "Inscription réussie.")

    return redirect('liste_evenements')
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