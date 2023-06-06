"""
    Handles signals sent within the smartserve app.
"""

from django import dispatch
from django.contrib import auth
from django.db.models import signals

from smartserve.models import Restaurant, User


def ready() -> None:
    """ Initialise this module when importing & starting signal listeners. """

    pass


@dispatch.receiver(signals.m2m_changed, sender=Restaurant.employees.through)
def user_added_to_restaurant(_sender, instance: User | Restaurant, action: str, reverse: bool, model: type[User | Restaurant], pk_set: set[int], **_kwargs) -> None:
    """
        Event handler for when a user is added to a restaurant's list of
        employees. The user's full name should be unique among that restaurant's
        employees.
    """

    if action == "post_add":
        if isinstance(instance, Restaurant) and not reverse:
            user: User
            # noinspection PyProtectedMember
            for user in model._base_manager.filter(id__in=pk_set):  # type: ignore
                if instance.employees.filter(first_name=user.first_name, last_name=user.last_name).exclude(id=user.id).exists():
                    instance.employees.remove(user)

        elif isinstance(instance, auth.get_user_model()) and reverse:
            restaurant: Restaurant
            # noinspection PyProtectedMember
            for restaurant in model._base_manager.filter(id__in=pk_set):  # type: ignore
                # noinspection PyUnresolvedReferences
                if restaurant.employees.filter(first_name=instance.first_name, last_name=instance.last_name).exclude(id=instance.id).exists():
                    restaurant.employees.remove(instance)
