from typing import Any, Iterator, Sequence

from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.auth.models import Group
from django.db import models
from django.db.models import Model, QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from rangefilter.filters import NumericRangeFilter

from smartserve.models import Restaurant, SeatBooking, Table, User, Seat, Booking


class UserIsStaffListFilter(admin.SimpleListFilter):
    """
        Admin filter to limit the :model:`smartserve.user` objects shown on the
        admin list view, by whether the user is a staff member.
    """

    title = _("Staff Member Status")
    parameter_name = "is_staff"

    def lookups(self, request: HttpRequest, model_admin: ModelAdmin) -> Sequence[tuple[str, Any]]:
        """
            Returns the sequence of pairs of url filter names & verbose filter
            names of the possible lookups.
        """

        return ("1", _("Is Staff Member")), ("0", _("Is Not Staff Member"))

    def queryset(self, request: HttpRequest, queryset: QuerySet[User]) -> QuerySet[User]:
        """ Returns the filtered queryset according to the given url lookup. """

        if self.value() == "1":
            return queryset.filter(is_staff=True)
        elif self.value() == "0":
            return queryset.filter(is_staff=False)
        else:
            return queryset


class UserGroupListFilter(admin.SimpleListFilter):
    """
        Admin filter to limit the :model:`smartserve.user` objects shown on the
        admin list view, by the user's group.
    """

    title = _("Group")
    parameter_name = "group"

    def lookups(self, request: HttpRequest, model_admin: ModelAdmin) -> Sequence[tuple[str, Any]]:
        """
            Returns the sequence of pairs of url filter names & verbose filter
            names of the possible lookups.
        """

        return tuple((str(group.pk), _(str(group.name))) for group in Group.objects.all())

    def queryset(self, request: HttpRequest, queryset: QuerySet[User]) -> QuerySet[User]:
        """ Returns the filtered queryset according to the given url lookup. """

        group_pk: str | None = self.value()
        if group_pk:
            return queryset.filter(groups=group_pk)
        else:
            return queryset


class UserIsActiveListFilter(admin.SimpleListFilter):
    """
        Admin filter to limit the :model:`smartserve.user` objects shown on the
        admin list view, by the user's active status.
    """

    title = _("Is Active Status")
    parameter_name = "is_active"

    def lookups(self, request: HttpRequest, model_admin: ModelAdmin) -> Sequence[tuple[str, Any]]:
        """
            Returns the sequence of pairs of url filter names & verbose filter
            names of the possible lookups.
        """

        return ("1", _("Is Active")), ("0", _("Is Not Active"))

    def queryset(self, request: HttpRequest, queryset: QuerySet[User]) -> QuerySet[User]:
        """ Returns the filtered queryset according to the given url lookup. """

        if self.value() == "1":
            return queryset.filter(is_active=True)
        elif self.value() == "0":
            return queryset.filter(is_active=False)
        else:
            return queryset


class RestaurantEmployeeCountListFilter(admin.ListFilter):
    """
        Admin filter to limit the :model:`smartserve.restaurant` objects shown
        on the admin list view, by the number of employees it has.
    """

    def __new__(cls, request: HttpRequest, params: dict[str, str], model: type[Model], model_admin: ModelAdmin) -> admin.ListFilter:  # type: ignore
        return NumericRangeFilter(  # type: ignore
            models.PositiveIntegerField(verbose_name=_("Number of Employees")),
            request,
            params,
            model,
            model_admin,
            field_path="_employee_count",
        )


class RestaurantTableCountListFilter(admin.ListFilter):
    """
        Admin filter to limit the :model:`smartserve.restaurant` objects shown
        on the admin list view, by the number of tables it has.
    """

    def __new__(cls, request: HttpRequest, params: dict[str, str], model: type[Model], model_admin: ModelAdmin) -> admin.ListFilter:  # type: ignore
        return NumericRangeFilter(  # type: ignore
            models.PositiveIntegerField(verbose_name=_("Number of Tables")),
            request,
            params,
            model,
            model_admin,
            field_path="_table_count",
        )


class TableIsSubTableFilter(admin.SimpleListFilter):
    """
        Admin filter to limit the :model:`smartserve.table` objects shown on the
        admin list view, by whether it is a sub-table or not.
    """

    title = _("Is Sub-Table")
    parameter_name = "is_sub_table"

    def lookups(self, request: HttpRequest, model_admin: ModelAdmin) -> Sequence[tuple[str | None, Any]]:
        """
            Returns the sequence of pairs of url filter names & verbose filter
            names of the possible lookups.
        """

        return (None, _("Is Not A Sub-Table")), ("1", _("Is A Sub-Table")), ("all", _("All"))

    def choices(self, changelist: Any) -> Iterator[dict[str, Any]]:
        lookup: str | None
        title: str
        for lookup, title in self.lookup_choices:
            yield {
                "selected": self.value() == lookup,
                "query_string": changelist.get_query_string(
                    {self.parameter_name: lookup},
                    []
                ),
                "display": title,
            }

    def queryset(self, request: HttpRequest, queryset: QuerySet[Table]) -> QuerySet[Table]:
        """ Returns the filtered queryset according to the given url lookup. """

        if self.value() is None:
            return queryset.filter(container_table__isnull=True)
        elif self.value() == "1":
            return queryset.filter(container_table__isnull=False)
        else:
            return queryset


class BaseRestaurantListFilter(admin.SimpleListFilter):
    """
        Admin filter to limit model objects shown on the admin list view, by the restaurant the object is associated
        with.
    """

    title = _("Restaurant")
    parameter_name = "restaurant"

    def lookups(self, request: HttpRequest, model_admin: ModelAdmin) -> Sequence[tuple[str, Any]]:
        """
            Returns the sequence of pairs of url filter names & verbose filter
            names of the possible lookups.
        """

        return tuple((str(restaurant.pk), _(str(restaurant.name))) for restaurant in Restaurant.objects.all())


class TableRestaurantListFilter(BaseRestaurantListFilter):
    """
        Admin filter to limit the :model:`smartserve.table` objects shown on the
        admin list view, by the restaurant the table is within.
    """

    def queryset(self, request: HttpRequest, queryset: QuerySet[Table]) -> QuerySet[Table]:
        """ Returns the filtered queryset according to the given url lookup. """

        restaurant_pk: str | None = self.value()
        if restaurant_pk:
            return queryset.filter(restaurant=restaurant_pk)
        else:
            return queryset


class SeatRestaurantListFilter(BaseRestaurantListFilter):
    """
        Admin filter to limit the :model:`smartserve.seat` objects shown on the
        admin list view, by the restaurant, the seat's table is within.
    """

    def queryset(self, request: HttpRequest, queryset: QuerySet[Seat]) -> QuerySet[Seat]:
        """ Returns the filtered queryset according to the given url lookup. """

        restaurant_pk: str | None = self.value()
        if restaurant_pk:
            return queryset.filter(table__restaurant=restaurant_pk)
        else:
            return queryset


class BookingRestaurantListFilter(BaseRestaurantListFilter):
    """
        Admin filter to limit the :model:`smartserve.booking` objects shown on the
        admin list view, by the restaurant, the booking's seats are within.
    """

    def queryset(self, request: HttpRequest, queryset: QuerySet[Booking]) -> QuerySet[Booking]:
        """ Returns the filtered queryset according to the given url lookup. """

        restaurant_pk: str | None = self.value()
        if restaurant_pk:
            return queryset.filter(seat_bookings__seat__table__restaurant=restaurant_pk)
        else:
            return queryset


class SeatBookingRestaurantListFilter(BaseRestaurantListFilter):
    # noinspection SpellCheckingInspection
    """
        Admin filter to limit the :model:`smartserve.seatbooking` objects shown
        on the admin list view, by the seat's restaurant.
    """

    def queryset(self, request: HttpRequest, queryset: QuerySet[SeatBooking]) -> QuerySet[SeatBooking]:
        """ Returns the filtered queryset according to the given url lookup. """

        restaurant_pk: str | None = self.value()
        if restaurant_pk:
            return queryset.filter(seat__table__restaurant=restaurant_pk)
        else:
            return queryset
