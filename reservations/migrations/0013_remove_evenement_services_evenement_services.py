# Generated by Django 5.2.1 on 2025-07-03 00:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0012_reservation_is_paid'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='evenement',
            name='services',
        ),
        migrations.AddField(
            model_name='evenement',
            name='services',
            field=models.CharField(blank=True, help_text='Liste des services séparés par des virgules', max_length=255),
        ),
    ]
