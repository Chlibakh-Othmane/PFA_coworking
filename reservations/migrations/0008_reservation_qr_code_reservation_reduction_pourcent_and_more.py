# Generated by Django 5.2.1 on 2025-06-26 00:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0007_remove_reservation_qr_code_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='qr_code',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='reservation',
            name='reduction_pourcent',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='reservation',
            name='services_utilises',
            field=models.ManyToManyField(blank=True, to='reservations.service'),
        ),
    ]
