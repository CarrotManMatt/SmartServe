from django.contrib import admin
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from knox.models import AuthToken

from smartserve.models import Seat, Table


class UserAuthTokensInline(admin.StackedInline):
    classes = ["collapse"]
    extra = 0
    model = AuthToken


class RestaurantTablesInline(admin.TabularInline):
    extra = 0
    model = Table
    verbose_name_plural = _("Tables (including Sub-Tables)")
    readonly_fields = ("true_number",)

    @admin.display(description=_("True Number"))
    def true_number(self, obj: Table | None) -> int | str:
        """
            Returns the true number of this table (following the container_table relation), to be displayed on the admin
            page.
        """

        if not obj or not obj.true_number:
            return admin.site.empty_value_display

        return obj.true_number


class TableSeatsInline(admin.StackedInline):
    extra = 0
    model = Seat
    verbose_name = _("Direct Seat")

    def has_add_permission(self, _request: HttpRequest, _obj: Seat | None) -> bool:
        return False
