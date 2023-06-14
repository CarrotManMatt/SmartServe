"""
    Admin configurations for models in smartserve app.
"""

from typing import Callable, Sequence

from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.db import models
from django.db.models import QuerySet
from django.forms import ModelForm
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from rangefilter.filters import DateTimeRangeFilter, DateTimeRangeFilterBuilder

from smartserve.models import Booking, Restaurant, Seat, Table, User
from .filters import BookingRestaurantListFilter, RestaurantEmployeeCountListFilter, RestaurantTableCountListFilter, SeatRestaurantListFilter, TableIsSubTableFilter, TableRestaurantListFilter, UserGroupListFilter, UserIsActiveListFilter, UserIsStaffListFilter
from .forms import UserChangeForm
from .inlines import BookingSeatBookingsInline, RestaurantTablesInline, TableSeatsInline, UserAuthTokensInline

admin.site.site_header = f"""SmartServe {_("Administration")}"""
admin.site.site_title = f"""SmartServe {_("Admin")}"""
admin.site.index_title = _("Overview")
admin.site.empty_value_display = "- - - - -"


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """
        Admin display configuration for :model:`smartserve.user` models, that
        adds the functionality to provide custom display configurations on the
        list, create & update pages.
    """

    form = UserChangeForm
    date_hierarchy = "date_joined"
    filter_horizontal = ("user_permissions",)
    fieldsets = (
        (None, {
            "fields": (
                "employee_id",
                ("first_name", "last_name"),
                "is_active",
                "restaurants"
            )
        }),
        ("Authentication", {
            "fields": ("date_joined", "last_login", "password"),
            "classes": ("collapse",)
        }),
        ("Permissions", {
            "fields": (
                "groups",
                "user_permissions",
                "is_staff",
                "is_superuser"
            ),
            "classes": ("collapse",)
        })
    )
    add_fieldsets = (
        (None, {
            "fields": (
                ("first_name", "last_name"),
                ("password1", "password2")
            )
        }),
        ("Extra", {
            "fields": ("is_active",),
            "classes": ("collapse",)
        }),
        ("Permissions", {
            "fields": (
                "groups",
                "user_permissions",
                "is_staff",
                "is_superuser"
            ),
            "classes": ("collapse",)
        })
    )
    inlines = (UserAuthTokensInline,)
    list_display = (
        "employee_id",
        "first_name",
        "last_name",
        "is_staff",
        "is_active"
    )
    list_display_links = ("employee_id",)
    list_editable = (
        "first_name",
        "last_name",
        "is_staff",
        "is_active"
    )
    list_filter = (
        UserIsStaffListFilter,
        UserGroupListFilter,
        UserIsActiveListFilter,
        ("date_joined", DateTimeRangeFilterBuilder(title=_("Date Joined"))),
        ("last_login", DateTimeRangeFilterBuilder(title=_("Last Login")))
    )
    autocomplete_fields = ("groups",)
    readonly_fields = (
        "employee_id",
        "password",
        "date_joined",
        "last_login"
    )
    search_fields = ("employee_id", "first_name", "last_name")
    ordering = ("first_name", "last_name")
    search_help_text = _("Search for an employee ID, first name or last name")

    @admin.display(description="Date Joined", ordering="date_joined")
    def date_joined(self, obj: User | None) -> str:
        """
            Returns the custom formatted string representation of the
            date_joined field, to be displayed on the admin page.
        """

        if not obj:
            return admin.site.empty_value_display

        return obj.date_joined.strftime("%d %b %Y %I:%M:%S %p")

    @admin.display(description="Last Login", ordering="last_login")
    def last_login(self, obj: User | None) -> str:
        """
            Returns the custom formatted string representation of the
            last_login field, to be displayed on the admin page.
        """

        if not obj or not obj.last_login:
            return admin.site.empty_value_display

        return obj.last_login.strftime("%d %b %Y %I:%M:%S %p")

    def get_form(self, *args, **kwargs) -> type[ModelForm]:
        """
            Return a Form class for use in the admin add view. This is used by
            add_view and change_view.

            Changes the labels on the form to remove unnecessary clutter.
        """

        kwargs.update(
            {
                "labels": {"password": _("Hashed password string")},
                "help_texts": {
                    "groups": None,
                    "user_permissions": None,
                    "is_staff": None,
                    "is_superuser": None,
                    "is_active": None
                }
            }
        )
        return super().get_form(*args, **kwargs)


@admin.register(Restaurant)
class RestaurantAdmin(ModelAdmin):
    fields = ("name", ("employee_count", "employees"), "table_count")
    list_display = ("name", "employee_count", "table_count")
    list_filter = (RestaurantEmployeeCountListFilter, RestaurantTableCountListFilter)
    inlines = (RestaurantTablesInline,)
    search_fields = ("name",)
    search_help_text = _("Search for a restaurant name")
    list_display_links = ("name",)
    readonly_fields = ("employee_count", "table_count")

    def get_queryset(self, request: HttpRequest) -> QuerySet[Restaurant]:
        """
            Return a QuerySet of all :model:`smartserve.restaurant` model
            instances that can be edited by the admin site. This is used by
            changelist_view.

            Adds the calculated annotated field "employee_count" to the
            queryset.
        """

        return super().get_queryset(request).annotate(  # type: ignore
            employee_count=models.Count("employees", distinct=True),
            table_count=models.Count("tables", distinct=True)
        )

    @admin.display(description=_("Number of Employees"), ordering="_employee_count")
    def employee_count(self, obj: Restaurant | None) -> int | str:
        """
            Returns the number of employees this restaurant has, to be displayed
            on the admin page.
        """

        if not obj:
            return admin.site.empty_value_display

        return obj.employee_count  # type: ignore

    @admin.display(description=_("Number of Tables (including Sub-Tables)"), ordering="_table_count")
    def table_count(self, obj: Restaurant | None) -> int | str:
        """
            Returns the number of tables this restaurant has, to be displayed
            on the admin page.
        """

        if not obj:
            return admin.site.empty_value_display

        return obj.table_count  # type: ignore


@admin.register(Table)
class TableAdmin(ModelAdmin):
    ordering = ("restaurant", "number")
    fields = (("number", "true_number"), "restaurant", "container_table")
    list_display = ("number", "restaurant", "container_table", "true_number")
    list_filter = (TableIsSubTableFilter, TableRestaurantListFilter)
    inlines = (TableSeatsInline,)
    search_fields = ("number", "restaurant__name", "container_table__number")
    search_help_text = _("Search for a table number or restaurant name")
    list_display_links = ("number",)
    list_editable = ("container_table",)
    autocomplete_fields = ("restaurant", "container_table")
    readonly_fields = ("true_number",)

    def get_list_filter(self, request: HttpRequest) -> Sequence[type[admin.ListFilter] | str | models.Field | tuple[str | models.Field, type[admin.FieldListFilter]] | list[str | models.Field | type[admin.FieldListFilter]]]:
        list_filter: Sequence[type[admin.ListFilter] | str | models.Field | tuple[str | models.Field, type[admin.FieldListFilter]] | list[str | models.Field | type[admin.FieldListFilter]]] = super().get_list_filter(request)

        if Restaurant.objects.count() > 15:
            list_filter = tuple(obj_filter for obj_filter in list_filter if obj_filter != TableRestaurantListFilter)

        return list_filter

    def get_list_display(self, request: HttpRequest) -> Sequence[str | Callable]:  # type: ignore
        list_display: Sequence[str | Callable] = super().get_list_display(request)

        if TableIsSubTableFilter.parameter_name not in request.GET:
            list_display = tuple(field for field in list_display if field != "container_table")

        return list_display

    def get_search_results(self, request: HttpRequest, queryset: QuerySet[Table], search_term: str) -> tuple[QuerySet[Table], bool]:
        # noinspection PyArgumentList
        if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest" and "/autocomplete/" in request.path and request.GET.get("model_name") == "table" and "Referer" in request.headers:
            split_referer_url: Sequence[str] = request.headers["Referer"].strip(r"/").split(r"/")
            if "table" in split_referer_url:
                try:
                    table_pk: int = int(split_referer_url[split_referer_url.index("table") + 1])
                except ValueError:
                    pass
                else:
                    queryset = queryset.exclude(pk=table_pk).filter(models.Q(container_table__isnull=True) | ~models.Q(container_table=table_pk))

                    try:
                        table: Table = Table.objects.get(pk=table_pk)
                    except Table.DoesNotExist:
                        pass
                    else:
                        queryset = queryset.filter(restaurant=table.restaurant)

            if "restaurant" in split_referer_url:
                try:
                    restaurant_pk: int = int(split_referer_url[split_referer_url.index("restaurant") + 1])
                except ValueError:
                    pass
                else:
                    queryset = queryset.filter(restaurant=restaurant_pk)

        return super().get_search_results(request, queryset, search_term)

    @admin.display(description=_("True Number"))
    def true_number(self, obj: Table | None) -> int | str:
        """
            Returns the true number of this table (following the container_table relation), to be displayed on the admin
            page.
        """

        if not obj or not obj.true_number:
            return admin.site.empty_value_display

        return obj.true_number


@admin.register(Seat)
class SeatAdmin(ModelAdmin):
    ordering = ("table", "location_index")
    list_display = ("location_index", "table")
    list_filter = (SeatRestaurantListFilter,)
    search_fields = ("table__number", "table__container_table__number", "table__restaurant__name")
    search_help_text = _("Search for a table number or restaurant name")
    list_editable = ("location_index", "table")
    list_display_links = None
    autocomplete_fields = ("table",)

    def get_list_filter(self, request: HttpRequest) -> Sequence[type[admin.ListFilter] | str | models.Field | tuple[str | models.Field, type[admin.FieldListFilter]] | list[str | models.Field | type[admin.FieldListFilter]]]:
        list_filter: Sequence[type[admin.ListFilter] | str | models.Field | tuple[str | models.Field, type[admin.FieldListFilter]] | list[str | models.Field | type[admin.FieldListFilter]]] = super().get_list_filter(request)

        if Restaurant.objects.count() > 15:
            list_filter = tuple(obj_filter for obj_filter in list_filter if obj_filter != SeatRestaurantListFilter)

        return list_filter

    def get_search_results(self, request: HttpRequest, queryset: QuerySet[Seat], search_term: str) -> tuple[QuerySet[Seat], bool]:
        # noinspection PyArgumentList,SpellCheckingInspection
        if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest" and "/autocomplete/" in request.path and request.GET.get("model_name") == "seatbooking" and "Referer" in request.headers:
            split_referer_url: Sequence[str] = request.headers["Referer"].strip(r"/").split(r"/")
            if "booking" in split_referer_url:
                try:
                    booking_pk: int = int(split_referer_url[split_referer_url.index("booking") + 1])
                except ValueError:
                    pass
                else:
                    try:
                        booking: Booking = Booking.objects.get(pk=booking_pk)
                    except Booking.DoesNotExist:
                        pass
                    else:
                        if booking.restaurant and booking.seat_bookings.count() > 1:
                            queryset = queryset.filter(table__restaurant=booking.restaurant)

        return super().get_search_results(request, queryset, search_term)


@admin.register(Booking)
class BookingAdmin(ModelAdmin):
    ordering = ("start",)
    fields = ("id", ("start", "end"), "restaurant")
    list_display = ("id", "start", "end", "restaurant")
    list_filter = (BookingRestaurantListFilter, ("start", DateTimeRangeFilter), ("end", DateTimeRangeFilter))
    inlines = (BookingSeatBookingsInline,)
    search_fields = ("seat_bookings__seat__table__number", "seat_bookings__seat__table__container_table__number", "seat_bookings__seat__table__restaurant__name")
    search_help_text = _("Search for a table number or restaurant name")
    list_display_links = ("id",)
    readonly_fields = ("id", "restaurant",)

    def get_list_filter(self, request: HttpRequest) -> Sequence[type[admin.ListFilter] | str | models.Field | tuple[str | models.Field, type[admin.FieldListFilter]] | list[str | models.Field | type[admin.FieldListFilter]]]:
        list_filter: Sequence[type[admin.ListFilter] | str | models.Field | tuple[str | models.Field, type[admin.FieldListFilter]] | list[str | models.Field | type[admin.FieldListFilter]]] = super().get_list_filter(request)

        if Restaurant.objects.count() > 15:
            list_filter = tuple(obj_filter for obj_filter in list_filter if obj_filter != BookingRestaurantListFilter)

        return list_filter

    @admin.display(description=_("Restaurant"))
    def restaurant(self, obj: Booking | None) -> Restaurant | str:
        """ Returns the restaurant the tables of this booking are within, to be displayed on the admin page. """

        if not obj or not obj.restaurant:
            return admin.site.empty_value_display

        return obj.restaurant
