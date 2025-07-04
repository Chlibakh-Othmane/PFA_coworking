# Generated by Django 5.2.1 on 2025-06-22 16:37

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Disponibilite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('heure_debut', models.TimeField()),
                ('heure_fin', models.TimeField()),
            ],
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100)),
                ('est_gratuit', models.BooleanField(default=False)),
                ('prix', models.DecimalField(decimal_places=2, default=0.0, max_digits=8)),
            ],
        ),
        migrations.CreateModel(
            name='Utilisateur',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('motDePasseHash', models.CharField(max_length=255)),
                ('role', models.CharField(choices=[('membre', 'Membre'), ('admin', 'Administrateur')], default='membre', max_length=10)),
                ('photoProfil', models.ImageField(blank=True, null=True, upload_to='photos/')),
                ('dateInscription', models.DateTimeField(default=django.utils.timezone.now)),
                ('tentativesConnexion', models.IntegerField(default=0)),
                ('estBloque', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Espace',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100)),
                ('capacite', models.IntegerField()),
                ('equipements', models.TextField(help_text='Liste des équipements, séparés par des virgules')),
                ('tarif_par_heure', models.DecimalField(decimal_places=2, max_digits=10)),
                ('disponibilites', models.ManyToManyField(related_name='espaces', to='reservations.disponibilite')),
            ],
        ),
        migrations.CreateModel(
            name='Reservation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_debut', models.DateTimeField()),
                ('date_fin', models.DateTimeField()),
                ('statut', models.CharField(choices=[('en_attente', 'En attente'), ('confirmee', 'Confirmée'), ('annulee', 'Annulée'), ('terminee', 'Terminée'), ('approuvee', 'Approuvée')], default='en_attente', max_length=20)),
                ('montant_total', models.FloatField(default=0.0)),
                ('qr_code', models.CharField(blank=True, max_length=255)),
                ('reduction_pourcent', models.FloatField(default=0.0)),
                ('espace', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='reservations.espace')),
                ('services_utilises', models.ManyToManyField(blank=True, to='reservations.service')),
                ('membre', models.ForeignKey(limit_choices_to={'role': 'membre'}, on_delete=django.db.models.deletion.CASCADE, to='reservations.utilisateur')),
            ],
        ),
        migrations.CreateModel(
            name='ServiceMateriel',
            fields=[
                ('service_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='reservations.service')),
                ('quantite_disponible', models.PositiveIntegerField(default=1)),
                ('garantie', models.BooleanField(default=False)),
                ('marque', models.CharField(blank=True, max_length=100)),
            ],
            bases=('reservations.service',),
        ),
        migrations.CreateModel(
            name='ServiceRestauration',
            fields=[
                ('service_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='reservations.service')),
                ('type_repas', models.CharField(choices=[('petit_dej', 'Petit Déjeuner'), ('dej', 'Déjeuner'), ('diner', 'Dîner'), ('snack', 'Snack'), ('boisson', 'Boisson')], max_length=20)),
            ],
            bases=('reservations.service',),
        ),
        migrations.CreateModel(
            name='Evenement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titre', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('categorie', models.CharField(max_length=50)),
                ('date_debut', models.DateTimeField()),
                ('date_fin', models.DateTimeField()),
                ('statut', models.CharField(choices=[('en_attente', 'En attente'), ('valide', 'Validé'), ('annule', 'Annulé')], default='en_attente', max_length=20)),
                ('capacite_max', models.PositiveIntegerField(default=20)),
                ('reservations', models.ManyToManyField(blank=True, to='reservations.reservation')),
                ('services', models.ManyToManyField(blank=True, related_name='espaces', to='reservations.service')),
                ('organisateur', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='reservations.utilisateur')),
                ('participants', models.ManyToManyField(blank=True, related_name='evenements_participes', to='reservations.utilisateur')),
            ],
        ),
    ]
