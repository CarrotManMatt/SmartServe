"""
    Handles signals sent within the smartserve app.
"""

from django import dispatch
from django.db import IntegrityError
from django.db.models import signals

from smartserve.models import Restaurant, User


def ready() -> None:
    """ Initialise this module when importing & starting signal listeners. """

    pass


# noinspection PyUnusedLocal
@dispatch.receiver(signals.m2m_changed, sender=Restaurant.employees.through)
def user_added_to_restaurant(sender, instance: User | Restaurant, action: str, reverse: bool, model: type[User | Restaurant], pk_set: set[int], **_kwargs) -> None:
    """
        Event handler for when a user is added to a restaurant's list of
        employees. The user's full name should be unique among that restaurant's
        employees.
    """

    if action == "pre_add":
        if isinstance(instance, Restaurant) and not reverse:
            user: User
            for user in model.objects.filter(id__in=pk_set):
                if instance.employees.filter(first_name=user.first_name, last_name=user.last_name).exclude(id=user.id).exists():
                    # noinspection PyProtectedMember
                    raise IntegrityError(f"UNIQUE constraint failed: {model._meta.app_label}_{model._meta.model_name}.first_name, {model._meta.app_label}_{model._meta.model_name}.last_name, {instance._meta.app_label}_{instance._meta.model_name}.id")

        elif isinstance(instance, User) and reverse:
            restaurant: Restaurant
            for restaurant in model.objects.filter(id__in=pk_set):
                if restaurant.employees.filter(first_name=instance.first_name, last_name=instance.last_name).exclude(id=instance.id).exists():
                    # noinspection PyProtectedMember
                    raise IntegrityError(f"UNIQUE constraint failed: {model._meta.app_label}_{model._meta.model_name}.first_name, {model._meta.app_label}_{model._meta.model_name}.last_name, {instance._meta.app_label}_{instance._meta.model_name}.id")
