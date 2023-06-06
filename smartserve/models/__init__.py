from typing import Callable

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import Permission, PermissionsMixin
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models
from django.db.models import Manager
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from . import utils
from .managers import UserManager
from .utils import AttributeDeleter, CustomBaseModel


class User(CustomBaseModel, AbstractBaseUser, PermissionsMixin):
    get_email_field_name = AttributeDeleter(object_name="User", attribute_name="get_email_field_name")  # type: ignore
    normalize_username = AttributeDeleter(object_name="User", attribute_name="normalize_username")  # type: ignore

    restaurants: Manager

    employee_id = models.CharField(
        _("Employee ID"),
        unique=True,
        max_length=6,
        validators=[RegexValidator(r"^\d+\Z"), MinLengthValidator(6)],
        default=utils.generate_employee_id,
        error_messages={
            "unique": _("A user with that ID already exists."),
        },
        blank=True
    )
    first_name = models.CharField(_("First Name"), max_length=75)
    last_name = models.CharField(_("Last Name"), max_length=75)
    is_staff = models.BooleanField(
        _("Is Admin?"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        _("Is Active?"),
        default=True,
        help_text=_("Designates whether this user should be treated as active. Unselect this instead of deleting accounts."),
    )
    date_joined = models.DateTimeField(_("Date Joined"), default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD: str = "employee_id"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = _("User")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._meta.get_field("password").error_messages = {
            "null": _("Password is a required field."),
            "blank": _("Password is a required field.")
        }
        self._meta.get_field("is_superuser").verbose_name = _("Is Superuser?")

    def __str__(self) -> str:
        return f"{self.employee_id} - {self.full_name}"

    def clean(self) -> None:
        if self.is_superuser:
            self.is_staff = True

        if not self.employee_id:
            self.employee_id = utils.generate_employee_id()

        # noinspection PyProtectedMember
        if self._meta.model._base_manager.filter(pk=self.pk).exists():
            restaurant: Restaurant
            for restaurant in self.restaurants.all():
                if restaurant.employees.filter(first_name=self.first_name, last_name=self.last_name).exclude(id=self.id).exists():
                    raise ValidationError(
                        {
                            "first_name": "An employee with that first & last name already exists at one of the restaurants that this employee is assigned to.",
                            "last_name": "An employee with that first & last name already exists at one of the restaurants that this employee is assigned to."
                        },
                        code="unique"
                    )

    @property
    def full_name(self) -> str:
        """ Return the first_name plus the last_name, with a space in between. """

        return f"{self.first_name} {self.last_name}"

    @property
    def short_name(self) -> str:
        """ Return the short name for the user. """

        return self.first_name

    get_full_name: Callable[["User"], str] = full_name
    get_short_name: Callable[["User"], str] = short_name

    def get_absolute_url(self) -> str:  # TODO
        raise NotImplementedError


class Restaurant(CustomBaseModel):
    name = models.CharField(
        _("Name"),
        max_length=100,
        validators=[RegexValidator(r"^[A-Za-z ]+\Z"), MinLengthValidator(2)]
    )
    employees = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="restaurants",
        verbose_name=_("Employees"),
        help_text=_("The set of employees at this restaurant. (Hold down “Control”, or “Command” on a Mac, to select more than one.)"),
        blank=True
    )

    class Meta:
        verbose_name = _("Restaurant")

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:  # TODO
        raise NotImplementedError


class Table(CustomBaseModel):
    number = models.PositiveIntegerField(
        _("Number")
    )
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="tables",
        verbose_name=_("Restaurant"),
        help_text=_("The restaurant that this table is within."),
        blank=False,
        null=False
    )
    container_table = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="sub_tables",
        verbose_name=_("Parent Container Table"),
        help_text=_("The reference to the parent container table, if this table object is a sub-table."),
        blank=True,
        null=True
    )

    @property
    def true_number(self) -> int:
        if self.container_table:
            return self.container_table.true_number
        else:
            return self.number

    class Meta:
        verbose_name = _("Table")
        constraints = [
            models.UniqueConstraint(
                fields=("number", "restaurant"),
                name="unique_restaurant_table_number"
            )
        ]

    def __str__(self) -> str:
        return f"Table {self.number} - {self.restaurant}"

    def clean(self) -> None:
        if self.container_table:
            if self.container_table == self:
                raise ValidationError({"container_table": _("The parent container table cannot be this own table.")}, code="invalid")

            if self.container_table.restaurant != self.restaurant:
                raise ValidationError({"container_table": _("Only tables at the same restaurant can be used as a parent container table.")}, code="invalid")

            def check_container_table_not_in_sub_tables(table: Table, container_table: Table) -> bool:
                if not table.sub_tables.all():
                    return True
                elif table.sub_tables.contains(container_table):
                    return False
                else:
                    return all(check_container_table_not_in_sub_tables(sub_table, container_table) for sub_table in table.sub_tables.all())

            if self.container_table and not check_container_table_not_in_sub_tables(self, self.container_table):
                raise ValidationError({"container_table": _("The parent container table cannot be a sub-table of this table.")}, code="invalid")
