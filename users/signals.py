from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

from .models import User


@receiver(post_save, sender=User)
def delete_auth_token(sender, instance, **kwargs):
    print('SIGNALS - User - post_save - delete_auth_token')
    if instance.is_deleted:
        print('SIGNALS - User - post_save - delete_auth_token - deleting Token')
        Token.objects.filter(user=instance).delete()  # Fixed!
