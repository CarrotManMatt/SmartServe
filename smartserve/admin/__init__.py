"""
    Admin configurations for models in smartserve app.
"""
from typing import Callable, Sequence

from django.contrib import admin, auth
from django.contrib.admin import ModelAdmin
from django.contrib.auth.admin import UserAdmin
from django.db import models
from django.db.models import QuerySet
from django.forms import ModelForm
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from rangefilter.filters import DateTimeRangeFilterBuilder

from smartserve.models import Restaurant, Table, User
from .filters import Employee_Count_List_Filter, Group_List_Filter, Restaurant_List_Filter, Staff_List_Filter, Table_Count_List_Filter, Table_Is_Sub_Table, User_Is_Active_List_Filter
from .forms import Custom_User_Change_Form
from .inlines import Auth_Tokens_Inline, Tables_Inline

admin.site.site_header = f"""SmartServe {_("Administration")}"""
admin.site.site_title = f"""SmartServe {_("Admin")}"""
admin.site.index_title = _("Overview")
admin.site.empty_value_display = "- - - - -"


@admin.register(auth.get_user_model())
class Custom_User_Admin(UserAdmin):
    """
        Admin display configuration for :model:`smartserve.user` models, that
        adds the functionality to provide custom display configurations on the
        list, create & update pages.
    """

    form = Custom_User_Change_Form
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
            "fields": ("display_date_joined", "display_last_login", "password"),
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
            "fields": ("is_active", "restaurants"),
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
    inlines = (Auth_Tokens_Inline,)
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
        Staff_List_Filter,
        Group_List_Filter,
        User_Is_Active_List_Filter,
        ("date_joined", DateTimeRangeFilterBuilder(title=_("Date Joined"))),
        ("last_login", DateTimeRangeFilterBuilder(title=_("Last Login")))
    )
    autocomplete_fields = ("groups",)
    readonly_fields = (
        "employee_id",
        "password",
        "display_date_joined",
        "display_last_login"
    )
    search_fields = ("employee_id", "first_name", "last_name")
    ordering = ("first_name", "last_name")
    search_help_text = _("Search for an employee ID, first name or last name")

    @admin.display(description="Date joined", ordering="date_joined")
    def display_date_joined(self, obj: User | None) -> str:
        """
            Returns the custom formatted string representation of the
            date_joined field, to be displayed on the admin page.
        """

        if not obj:
            return admin.site.empty_value_display

        return obj.date_joined.strftime("%d %b %Y %I:%M:%S %p")

    @admin.display(description="Last login", ordering="last_login")
    def display_last_login(self, obj: User | None) -> str:
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
class Restaurant_Admin(ModelAdmin):
    fields = ("name", ("employee_count", "employees"), "table_count")
    filter_horizontal = ("employees",)
    list_display = ("name", "employee_count", "table_count")
    list_filter = (Employee_Count_List_Filter, Table_Count_List_Filter)
    inlines = (Tables_Inline,)
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
            _employee_count=models.Count("employees", distinct=True),
            _table_count=models.Count("tables", distinct=True)
        )

    @admin.display(description=_("Number of Employees"), ordering="_employee_count")
    def employee_count(self, obj: Restaurant | None) -> int | str:
        """
            Returns the number of employees this restaurant has, to be displayed
            on the admin page.
        """

        if not obj:
            return admin.site.empty_value_display

        # noinspection PyProtectedMember
        return obj._employee_count  # type: ignore

    @admin.display(description=_("Number of Tables (including Sub-Tables)"), ordering="_table_count")
    def table_count(self, obj: Restaurant | None) -> int | str:
        """
            Returns the number of tables this restaurant has, to be displayed
            on the admin page.
        """

        if not obj:
            return admin.site.empty_value_display

        # noinspection PyProtectedMember
        return obj._table_count  # type: ignore


@admin.register(Table)
class Table_Admin(ModelAdmin):
    ordering = ("restaurant", "number")
    fields = ("number", "restaurant", "container_table")
    list_display = ("number", "restaurant", "container_table")
    list_filter = (Table_Is_Sub_Table, Restaurant_List_Filter)
    search_fields = ("number", "restaurant__name", "container_table__number")
    search_help_text = _("Search for a table number or restaurant name")
    list_display_links = ("number",)
    list_editable = ("restaurant", "container_table")
    autocomplete_fields = ("restaurant", "container_table")

    def get_queryset(self, request: HttpRequest) -> QuerySet[Table]:
        return self.model.objects.all_with_sub_tables()  # type: ignore

    def get_list_filter(self, request: HttpRequest) -> Sequence[type[admin.ListFilter] | str | models.Field | tuple[str | models.Field, type[admin.FieldListFilter]] | list[str | models.Field | type[admin.FieldListFilter]]]:
        list_filter: Sequence[type[admin.ListFilter] | str | models.Field | tuple[str | models.Field, type[admin.FieldListFilter]] | list[str | models.Field | type[admin.FieldListFilter]]] = super().get_list_filter(request)

        if Restaurant.objects.count() > 15:
            list_filter = tuple(obj_filter for obj_filter in list_filter if obj_filter != Restaurant_List_Filter)

        return list_filter

    def get_list_display(self, request: HttpRequest) -> Sequence[str | Callable]:  # type: ignore
        list_display: Sequence[str | Callable] = super().get_list_display(request)

        if Table_Is_Sub_Table.parameter_name not in request.GET:
            list_display = tuple(field for field in list_display if field != "container_table")

        return list_display

    def get_search_results(self, request: HttpRequest, queryset: QuerySet[Table], search_term: str) -> tuple[QuerySet[Table], bool]:
        if "Referer" in request.headers and "/admin/smartserve/table/" in request.headers["Referer"]:
            print(queryset)
            try:
                table_pk: int = int(request.headers["Referer"].split(r"/")[-2])
            except ValueError:
                pass
            else:
                queryset = queryset.exclude(pk=table_pk)
                print(queryset)

                try:
                    table: Table = Table.objects.all_with_sub_tables().get(pk=table_pk)
                except Table.DoesNotExist:
                    pass
                else:
                    queryset = queryset.filter(models.Q(container_table__isnull=True) | models.Q(container_table__isnull=False, container_table__restaurant__pk=table.restaurant.pk))

        return super().get_search_results(request, queryset, search_term)
