from datetime import datetime
from typing import Callable

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import Permission, PermissionsMixin
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Manager, Model, QuerySet
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
        validators=[
            RegexValidator(r"^\d+\Z", _("The Employee ID must be a 6 digit number.")),
            MinLengthValidator(6, _("The Employee ID must be 6 digits."))
        ],
        default=utils.generate_employee_id,
        error_messages={
            "unique": _("A user with that Employee ID already exists."),
            "max_length": _("The Employee ID must be 6 digits.")
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

        if self.pk:
            restaurant: Restaurant
            for restaurant in self.restaurants.all():
                if restaurant.employees.filter(first_name=self.first_name, last_name=self.last_name).exclude(pk=self.pk).exists():
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
        validators=[RegexValidator(r"^(?![\s'])(?!.*[\s']{2})[A-Za-z ']+(?<![\s'])\Z"), MinLengthValidator(2)]
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
        _("Number"),
        validators=[MinValueValidator(1)]
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

    @property
    def seats(self) -> QuerySet["Seat"]:
        def get_sub_table_seats(table: Table) -> QuerySet[Seat]:
            # noinspection PyProtectedMember
            seats: QuerySet[Seat] = table._seats.all()

            if table.sub_tables.exists():
                sub_table: Table
                for sub_table in table.sub_tables.all():
                    seats = seats | get_sub_table_seats(sub_table)

            return seats

        if not self.container_table:
            return get_sub_table_seats(self)

        else:
            return self._seats.all()

    @property
    def bookings(self) -> QuerySet["Booking"]:
        return Booking.objects.filter(pk__in=self.seats.values_list("seat_bookings__booking__pk", flat=True))

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

    def get_absolute_url(self) -> str:  # TODO
        raise NotImplementedError

    def clean(self) -> None:
        if self.container_table:
            if self.container_table == self:
                raise ValidationError({"container_table": _("The parent container table cannot be this own table.")}, code="invalid")

            if self.container_table.restaurant != self.restaurant:
                raise ValidationError({"container_table": _("Only tables at the same restaurant can be used as a parent container table.")}, code="invalid")

            def check_container_table_not_in_sub_tables(table: Table, container_table: Table) -> bool:
                if not table.sub_tables.exists():
                    return True
                elif table.sub_tables.contains(container_table):
                    return False
                else:
                    return all(check_container_table_not_in_sub_tables(sub_table, container_table) for sub_table in table.sub_tables.all())

            if self.pk and not check_container_table_not_in_sub_tables(self, self.container_table):
                raise ValidationError({"container_table": _("The parent container table cannot be a sub-table of this table.")}, code="invalid")

    def create_booking(self, start: datetime, end: datetime) -> "Booking":
        booking: Booking = Booking.objects.create(start=start, end=end)

        seat: Seat
        for seat in self.seats.all():
            SeatBooking.objects.create(seat=seat, booking=booking)

        booking.refresh_from_db()
        return booking


class Seat(CustomBaseModel):
    table = models.ForeignKey(
        Table,
        on_delete=models.CASCADE,
        related_name="_seats",
        verbose_name=_("Table"),
        help_text=_("The Table this seat is at."),
        blank=False,
        null=False
    )
    location_index = models.PositiveIntegerField(
        _("Location Index"),
        null=False,
        blank=False
    )

    class Meta:
        verbose_name = _("Seat")
        constraints = [
            models.UniqueConstraint(
                fields=("table", "location_index"),
                name="unique_table_location_index"
            )
        ]

    def __str__(self) -> str:
        return f"Seat {self.location_index} - Table {self.table.number}"

    def get_absolute_url(self) -> str:  # TODO
        raise NotImplementedError


class Booking(CustomBaseModel):
    start = models.DateTimeField(_("Start Date & Time"))
    end = models.DateTimeField(_("End Date & Time"))

    @property
    def tables(self) -> QuerySet[Table]:
        if not self.pk:
            raise ValueError(f"{self.__class__.__name__!r} instance needs to have a primary key value before this relationship can be used.")

        return Table.objects.filter(pk__in=self.seat_bookings.values_list("seat__table__pk", flat=True))

    @property
    def restaurant(self) -> Restaurant | None:
        if not self.tables.exists():
            return None

        return self.tables.first().restaurant

    class Meta:
        verbose_name = _("Booking")
        constraints = [
            models.CheckConstraint(
                check=models.Q(end__gt=models.F("start")),
                name="check_start_end",
                violation_error_message=_("Start Date & Time must be before End Date & Time.")
            )
        ]

    def __str__(self) -> str:
        return f"Booking {self.id}"

    def get_absolute_url(self) -> str:  # TODO
        raise NotImplementedError


class SeatBooking(CustomBaseModel):
    seat = models.ForeignKey(
        Seat,
        on_delete=models.PROTECT,
        related_name="seat_bookings",
        verbose_name=_("Seat"),
        help_text=_("The Seat that this is a booking for."),
        blank=False,
        null=False
    )
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="seat_bookings",
        verbose_name=_("Booking"),
        help_text=_("The overall Booking that this Seat Booking is a part of."),
        blank=False,
        null=False
    )

    class Meta:
        verbose_name = _("Seat Booking")
        constraints = [
            models.UniqueConstraint(
                fields=("seat", "booking"),
                name="unique_seat_booking"
            )
        ]

    def clean(self) -> None:
        if self.booking.pk and self.booking.restaurant and self.seat.table.restaurant != self.booking.restaurant:
            raise ValidationError("The tables within this Booking must all be at the same restaurant", code="invalid")

        if SeatBooking.objects.exclude(booking=self.booking).filter(seat__table=self.seat.table).exclude(booking__start__gte=self.booking.end).exclude(booking__end__lte=self.booking.start).exists():
            raise ValidationError({"seat": "A booking for this seat's table already exists within these start & end points."}, code="unique")
