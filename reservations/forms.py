from django import forms
from django.contrib.auth import authenticate
from .models import Reservation, Avis, Espace, Utilisateur,Evenement

# Connexion avec email + mot de passe
class ConnexionForm(forms.Form):
    email = forms.EmailField()
    mot_de_passe = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        self.user = None
        super().__init__(*args, **kwargs)

    def clean(self):
        email = self.cleaned_data.get('email')
        mot_de_passe = self.cleaned_data.get('mot_de_passe')
        if email and mot_de_passe:
            try:
                utilisateur = Utilisateur.objects.get(email=email)
            except Utilisateur.DoesNotExist:
                raise forms.ValidationError("Email ou mot de passe incorrect.")

            utilisateur = authenticate(username=email, password=mot_de_passe)
            if utilisateur is None:
                raise forms.ValidationError("Email ou mot de passe incorrect.")
            self.user = utilisateur
        return self.cleaned_data

    def get_user(self):
        return self.user

# Formulaire de réservation
class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['date_debut', 'date_fin']
        widgets = {
            'date_debut': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'date_fin': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }
# Formulaire d'avis
class AvisForm(forms.ModelForm):
    class Meta:
        model = Avis
        fields = ['note', 'commentaire']
        widgets = {
            'note': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'commentaire': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

# Formulaire pour ajouter/modifier un espace
class EspaceForm(forms.ModelForm):
    class Meta:
        model = Espace
        fields = ['nom', 'capacite', 'equipements', 'tarif_par_heure', 'image']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Creators Space'
            }),
            'capacite': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 70'
            }),
            'equipements': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ex: Wifi, Cafetière, Écran 4K...'
            }),
            'tarif_par_heure': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 25.00'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
        labels = {
            'nom': "Nom de l'espace",
            'capacite': "Capacité (personnes)",
            'equipements': "Équipements (séparés par des virgules)",
            'tarif_par_heure': "Tarif horaire (MAD)",
            'image': "Photo de l'espace"
        }

# Formulaire d'inscription
class InscriptionForm(forms.ModelForm):
    mot_de_passe = forms.CharField(widget=forms.PasswordInput(), label="Mot de passe")

    class Meta:
        model = Utilisateur
        fields = ['first_name', 'last_name', 'email', 'mot_de_passe', 'role', 'photoProfil']
        labels = {
            'first_name': 'Nom',
            'last_name': 'Prénom',
            'photoProfil': 'Photo de profil',
            'role': 'Rôle'
        }
        widgets = {
            'photoProfil': forms.ClearableFileInput(attrs={'accept': 'image/*'})
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['mot_de_passe'])
        
        # Générer un username à partir de l'email
        if not user.username:
            user.username = self.cleaned_data['email'].split('@')[0]
        
        # Vérification de la photo de profil
        if not user.photoProfil:
            # Vous pouvez définir une image par défaut ici si nécessaire
            # user.photoProfil = 'chemin/vers/image_par_defaut.jpg'
            pass
            
        if commit:
            user.save()
        return user
# Formulaire pour modifier un profil
class ModifierProfilForm(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = ['first_name', 'last_name', 'email', 'role', 'photoProfil']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),  # Ajout du select pour le rôle
            'photoProfil': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'first_name': 'Nom',
            'last_name': 'Prénom',
            'role': 'Rôle',
            'photoProfil': 'Photo de profil'
        }
class EvenementForm(forms.ModelForm):
    class Meta:
        model = Evenement
        exclude = ['statut', 'organisateur', 'participants', 'reservations']