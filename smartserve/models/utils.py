"""
    Utility classes & functions provided for all models within smartserve app.
"""
from typing import Any, Collection, Self

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRel, GenericRelation
from django.db import models
from django.db.models import ForeignObjectRel, ManyToManyField, ManyToManyRel, ManyToOneRel, Model


class Custom_Base_Model(Model):
    """
        Base model that provides extra utility methods for all other models to
        use.

        This class is abstract so should not be instantiated or have a table
        made for it in the database (see
        https://docs.djangoproject.com/en/stable/topics/db/models/#abstract-base-classes).
    """

    class Meta:
        abstract = True

    def refresh_from_db(self, using: str | None = None, fields: Collection[str] | None = None, deep: bool = True) -> None:
        """
            Custom implementation of refreshing in-memory objects from the
            database, which also updates any related fields on this object. The
            fields to update can be limited with the "fields" argument, and
            whether to update related objects or not can be specified with the
            "deep" argument.

            Uses django's argument structure which cannot be changed (see
            https://docs.djangoproject.com/en/stable/ref/models/instances/#django.db.models.Model.refresh_from_db).
        """

        fields_set: set[str] | None = None

        if fields:  # NOTE: Remove duplicate field names from fields parameter
            fields_set = set(fields)

        super().refresh_from_db(using=using, fields=list(fields_set) if fields_set else None)

        if deep:  # NOTE: Refresh any related fields/objects if requested
            updated_model: Model = self._meta.model.objects.get(id=self.id)  # type: ignore

            field: models.Field | ForeignObjectRel | GenericForeignKey
            for field in self.get_single_relation_fields():  # type: ignore
                if not fields_set or field.name in fields_set:  # NOTE: Limit the fields to update by the provided list of field names
                    setattr(self, field.name, getattr(updated_model, field.name))

            for field in self.get_multi_relation_fields():  # type: ignore  # BUG: Relation fields not of acceptable type are not refreshed
                if not fields_set or field.name in fields_set:  # NOTE: Limit the fields to update by the provided list of field names
                    pass

    def save(self, *args, **kwargs) -> None:
        """
            Saves the current instance to the database, only after the model
            has been cleaned. This ensures any data in the database is valid,
            even if the data was not added via a ModelForm (E.g. data is added
            using the ORM API).

            Uses django's argument structure which cannot be changed (see
            https://docs.djangoproject.com/en/stable/ref/models/instances/#django.db.models.Model.save).
        """

        self.full_clean()

        super().save(*args, **kwargs)

    def update(self, using: str | None = None, *, commit: bool = True, **kwargs) -> None:
        """
            Changes an in-memory object's values & save that object to the
            database all in one operation (based on Django's
            Queryset.bulk_update method).
        """

        key: str
        value: Any
        for key, value in kwargs.items():
            if key not in self.get_proxy_field_names():  # NOTE: Given field name must be a proxy field name or an actual field name
                self._meta.get_field(key)  # NOTE: Attempt to get the field by its name (will raise FieldDoesNotExist if no field exists with that name for this model)
            setattr(self, key, value)

        if commit:
            if using:
                self.save(using)
            else:
                self.save()

    @classmethod
    def get_proxy_field_names(cls) -> set[str]:
        """
            Returns a set of names of extra properties of this model that can
            be saved to the database, even though those fields don't actually
            exist. They are just proxy fields.
        """

        return set()

    @classmethod
    def get_non_relation_fields(cls, *, names: bool = False) -> set[models.Field] | set[str]:
        """
            Helper function to return an iterable of all the standard
            non-relation fields or field names of this model.
        """

        non_relation_fields: set[models.Field] = {field for field in cls._meta.get_fields() if field.name != "+" and not field.is_relation}  # type: ignore

        if names:
            return {field.name for field in non_relation_fields}
        else:
            return non_relation_fields

    @classmethod
    def get_single_relation_fields(cls, *, names: bool = False) -> set[models.Field | ForeignObjectRel | GenericForeignKey] | set[str]:
        """
            Helper function to return an iterable of all the forward single
            relation fields or field names of this model.
        """

        single_relation_fields: set[models.Field | ForeignObjectRel | GenericForeignKey] = {field for field in cls._meta.get_fields() if field.name != "+" and field.is_relation and not isinstance(field, ManyToManyField) and not isinstance(field, ManyToManyRel) and not isinstance(field, ManyToOneRel) and not isinstance(field, GenericRelation) and not isinstance(field, GenericRel)}

        if names:
            return {field.name for field in single_relation_fields}
        else:
            return single_relation_fields

    @classmethod
    def get_multi_relation_fields(cls, *, names: bool = False) -> set[models.Field | ForeignObjectRel | GenericForeignKey] | set[str]:
        """
            Helper function to return an iterable of all the forward
            many-to-many relation fields or field names of this model.
        """

        multi_relation_fields: set[models.Field | ForeignObjectRel | GenericForeignKey] = {field for field in cls._meta.get_fields() if field.name != "+" and field.is_relation and (isinstance(field, ManyToManyField) or isinstance(field, ManyToManyRel) or isinstance(field, ManyToOneRel) or isinstance(field, GenericRelation) or isinstance(field, GenericRel))}

        if names:
            return {field.name for field in multi_relation_fields}
        else:
            return multi_relation_fields


class Attribute_Deleter:
    def __init__(self, object_name: str, attribute_name: str) -> None:
        self.object_name: str = object_name
        self.attribute_name: str = attribute_name

    def __get__(self, instance: object, owner: object) -> Self:
        raise AttributeError(f"type object '{self.object_name}' has no attribute '{self.attribute_name}'")
