"""
    Utility classes & functions provided for all models within smartserve app.
"""

import uuid
from typing import Any, Self

from django.core.exceptions import FieldDoesNotExist
from django.db.models import Model


def generate_employee_id() -> str:
    return str(uuid.uuid4().int)[:6]


class AttributeDeleter:
    def __init__(self, object_name: str, attribute_name: str) -> None:
        self.object_name: str = object_name
        self.attribute_name: str = attribute_name

    def __get__(self, instance: object, owner: object) -> Self:
        raise AttributeError(f"type object '{self.object_name}' has no attribute '{self.attribute_name}'")


class CustomBaseModel(Model):
    """
        Base model that provides extra utility methods for all other models to
        use.

        This class is abstract so should not be instantiated or have a table
        made for it in the database (see
        https://docs.djangoproject.com/en/stable/topics/db/models/#abstract-base-classes).
    """

    class Meta:
        abstract = True

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        proxy_fields: dict[str, Any] = {field_name: kwargs.pop(field_name) for field_name in set(kwargs.keys()) & self.get_proxy_field_names()}  # TODO: Fix code smell

        super().__init__(*args, **kwargs)

        proxy_field_name: str
        value: Any
        for proxy_field_name, value in proxy_fields.items():
            setattr(self, proxy_field_name, value)

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
            Saves the current instance to the database, only after the model
            has been cleaned. This ensures any data in the database is valid,
            even if the data was not added via a ModelForm (E.g. data is added
            using the ORM API).

            Uses django's argument structure, which cannot be changed (see
            https://docs.djangoproject.com/en/stable/ref/models/instances/#django.db.models.Model.save).
        """

        self.full_clean()

        super().save(*args, **kwargs)

    def update(self, commit: bool = True, using: str | None = None, **kwargs: Any) -> None:
        """
            Changes an in-memory object's values & save that object to the
            database all in one operation (based on Django's
            Queryset.bulk_update method).
        """

        unexpected_kwargs: set[str] = set()

        field_name: str
        for field_name in set(kwargs.keys()) - self.get_proxy_field_names():  # TODO: Fix code smell
            try:
                # noinspection PyUnresolvedReferences
                self._meta.get_field(field_name)
            except FieldDoesNotExist:
                unexpected_kwargs.add(field_name)

        if unexpected_kwargs:
            raise TypeError(f"{self._meta.model.__name__} got unexpected keyword arguments: {tuple(unexpected_kwargs)}")

        value: Any
        for field_name, value in kwargs.items():
            setattr(self, field_name, value)

        if commit:
            self.save(using)

    update.alters_data = True  # type: ignore

    @classmethod
    def get_proxy_field_names(cls) -> set[str]:
        """
            Returns a set of names of extra properties of this model that can
            be saved to the database, even though those fields don't actually
            exist. They are just proxy fields.
        """

        return set()
