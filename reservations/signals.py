from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.signals import valid_ipn_received
from django.dispatch import receiver
from .models import Reservation

@receiver(valid_ipn_received)
def paiement_paypal_valide(sender, **kwargs):
    ipn = sender
    if ipn.payment_status == ST_PP_COMPLETED:
        try:
            item_name = ipn.item_name
            montant = ipn.mc_gross

            # Vérifie la réservation avec le même montant
            reservation = Reservation.objects.filter(montant_total=montant, payee=False).last()

            if reservation:
                reservation.payee = True
                reservation.save()
                print(" Paiement reçu et réservation marquée comme payée")
        except Exception as e:
            print("Erreur IPN :", e)
