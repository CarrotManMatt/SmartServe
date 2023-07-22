from datetime import datetime
from typing import Any, Callable

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

    def __init__(self, *args: Any, **kwargs: Any) -> None:
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
        validators=[RegexValidator(r"^(?![\s'-])(?!.*[\s'-]{2})[A-Za-z '-]+(?<![\s'-])\Z"), MinLengthValidator(2)]
    )
    employees = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="restaurants",
        verbose_name=_("Employees"),
        help_text=_("The set of employees at this restaurant."),
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
        validators=[MinValueValidator(1)],
        null=False,
        blank=False
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

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        class SeatManager(Manager):
            def __init__(self, table: Table):
                self.table: Table = table

                super().__init__()

            def get_queryset(self) -> QuerySet[Seat]:  # type: ignore
                if not self.table.container_table:
                    return self.get_sub_table_seats(self.table)
                else:
                    # noinspection PyProtectedMember
                    return self.table._seats.all()

            @classmethod
            def get_sub_table_seats(cls, table: Table) -> QuerySet[Seat]:
                # noinspection PyProtectedMember
                seats: QuerySet[Seat] = table._seats.all()

                if table.sub_tables.exists():
                    sub_table: Table
                    for sub_table in table.sub_tables.all():
                        seats = seats | cls.get_sub_table_seats(sub_table)

                return seats

        self.seats: SeatManager = SeatManager(table=self)

        class BookingManager(Manager):
            def __init__(self, seats: Manager[Seat]):
                self.seats: Manager[Seat] = seats

                super().__init__()

            def get_queryset(self) -> QuerySet[Booking]:  # type: ignore
                return Booking.objects.filter(pk__in=self.seats.values_list("seat_bookings__booking__pk", flat=True))

        self.bookings: BookingManager = BookingManager(self.seats)

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
        validators=[MinValueValidator(0)],
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
    start = models.DateTimeField(
        _("Start Date & Time"),
        blank=False,
        null=False
    )
    end = models.DateTimeField(
        _("End Date & Time"),
        blank=False,
        null=False
    )

    @property
    def restaurant(self) -> Restaurant | None:
        if not self.tables.exists():
            return None

        return self.tables.first().restaurant  # type: ignore

    class Meta:
        verbose_name = _("Booking")
        constraints = [
            models.CheckConstraint(
                check=models.Q(end__gt=models.F("start")),
                name="check_start_end",
                violation_error_message=_("Start Date & Time must be before End Date & Time.")
            )
        ]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        class TableManager(Manager):
            def __init__(self, seat_bookings: Manager[SeatBooking]):
                self.seat_bookings: Manager[SeatBooking] = seat_bookings

                super().__init__()

            def get_queryset(self) -> QuerySet[Table]:  # type: ignore
                return Table.objects.filter(pk__in=self.seat_bookings.values_list("seat__table__pk", flat=True))

        self.tables: TableManager = TableManager(self.seat_bookings)

        class OrderManager(Manager):
            def __init__(self, seat_bookings: Manager[SeatBooking]):
                self.seat_bookings: Manager[SeatBooking] = seat_bookings

                super().__init__()

            def get_queryset(self) -> QuerySet[Order]:  # type: ignore
                return Order.objects.filter(seat_booking__in=self.seat_bookings.values_list(flat=True))

        self.orders: OrderManager = OrderManager(self.seat_bookings)

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
    ordered_menu_items = models.ManyToManyField(
        "MenuItem",
        related_name="+",
        verbose_name=_("Ordered Menu Items"),
        help_text=_("The set of menu items ordered by this seat booking."),
        blank=True,
        through="Order",
        through_fields=("seat_booking", "menu_item")
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
        if self.seat_id and self.booking_id and self.booking.restaurant and self.booking.seat_bookings.count() >= 2 and self.seat.table.restaurant != self.booking.restaurant:
            raise ValidationError("The tables within this Booking must all be at the same restaurant.", code="invalid")

        if self.booking_id and self.seat_id and SeatBooking.objects.exclude(booking=self.booking).filter(seat__table=self.seat.table).exclude(booking__start__gte=self.booking.end).exclude(booking__end__lte=self.booking.start).exists():
            raise ValidationError({"seat": "A booking for this seat's table already exists within these start & end points."}, code="unique")

    def __str__(self) -> str:
        return f"{self.seat} at {self.booking}"


class MenuItem(CustomBaseModel):
    name = models.CharField(
        _("Name"),
        max_length=100,
        validators=[RegexValidator(r"^(?![\s'-])(?!.*[\s'-]{2})[A-Za-z '-]+(?<![\s'-])\Z"), MinLengthValidator(2)],
        unique=True
    )
    description = models.TextField(
        _("Description"),
        max_length=200,
        error_messages={"null": "Description field cannot be null, use an empty string instead."},
        null=False,
        blank=True,
        help_text="Longer textfield containing a description of this menu item."
    )
    available_at_restaurants = models.ManyToManyField(
        Restaurant,
        related_name="menu_items",
        verbose_name=_("Available At Restaurants"),
        help_text=_("The set of restaurants that this menu item is available at."),
        blank=True
    )

    class Meta:
        verbose_name = _("Menu Item")

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:  # TODO
        raise NotImplementedError


class Order(CustomBaseModel):
    class Courses(models.IntegerChoices):
        """ Enum of course number & display values of each course. """

        APPETISER = 0, _("Appetiser")
        STARTER = 1, _("Starter")
        MAIN_COURSE = 2, _("Main Course")
        DESSERT = 3, _("Dessert")

    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.PROTECT,
        related_name="orders"
    )
    seat_booking = models.ForeignKey(
        SeatBooking,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    course = models.PositiveIntegerField(
        _("Course"),
        null=False,
        blank=False,
        choices=Courses.choices
    )
    notes = models.TextField(
        _("Notes"),
        max_length=200,
        error_messages={"null": "Notes field cannot be null, use an empty string instead."},
        null=False,
        blank=True,
        help_text="Longer textfield containing any notes to the kitchen about how to prepare this order."
    )

    class Meta:
        verbose_name = _("Ordered Menu Item")

    def __str__(self) -> str:
        return f"{self.menu_item} for {self.seat_booking.seat}"

    def clean(self) -> None:
        if self.seat_booking_id and self.menu_item_id and self.seat_booking.seat.table.restaurant not in self.menu_item.available_at_restaurants.all():
            raise ValidationError({"menu_item": "Only menu items at this booking's restaurant can be ordered."}, code="invalid")

    def get_absolute_url(self) -> str:  # TODO
        raise NotImplementedError
