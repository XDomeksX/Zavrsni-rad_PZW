from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Category


def ensure_inbox_for_user(user):
    Category.objects.get_or_create(
        owner=user,
        is_inbox=True,
        defaults={"name": "Inbox"},
    )


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_inbox_category(sender, instance, created, **kwargs):
    if created:
        ensure_inbox_for_user(instance)
