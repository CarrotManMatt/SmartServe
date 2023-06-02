from typing import Any, Sequence, Type

from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.auth.models import Group
from django.db import models
from django.db.models import Model, QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from rangefilter.filters import NumericRangeFilter

from smartserve.models import User


class Staff_List_Filter(admin.SimpleListFilter):
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


class Group_List_Filter(admin.SimpleListFilter):
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

        return tuple((str(group.id), _(str(group.name))) for group in Group.objects.all())

    def queryset(self, request: HttpRequest, queryset: QuerySet[User]) -> QuerySet[User]:
        """ Returns the filtered queryset according to the given url lookup. """

        group_id: str | None = self.value()
        if group_id is not None:
            return queryset.filter(groups=group_id)
        else:
            return queryset


class User_Is_Active_List_Filter(admin.SimpleListFilter):
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


class Employee_Count_List_Filter(admin.ListFilter):
    """
        Admin filter to limit the :model:`smartserve.restaurant` objects shown
        on the admin list view, by the number of employees it has.
    """

    def __new__(cls, request: HttpRequest, params: dict[str, str], model: Type[Model], model_admin: ModelAdmin) -> admin.ListFilter:  # type: ignore
        return NumericRangeFilter(  # type: ignore
            models.PositiveIntegerField(verbose_name=_("Number of Employees")),
            request,
            params,
            model,
            model_admin,
            field_path="_employee_count",
        )
