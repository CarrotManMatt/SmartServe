"""
    Admin configurations for models in smartserve app.
"""

from typing import Sequence, Type

from django.contrib import admin, auth
from django.contrib.auth.admin import UserAdmin
from django.forms import BaseModelForm

from smartserve.models import User

admin.site.site_header = "SmartServe Administration"
admin.site.site_title = "SmartServe Admin"
admin.site.index_title = "Overview"
admin.site.empty_value_display = "- - - - -"


@admin.register(auth.get_user_model())
class Custom_User_Admin(UserAdmin):
    """
        Admin display configuration for :model:`smartserve.user` models, that
        adds the functionality to provide custom display configurations on the
        list, create & update pages.
    """

    date_hierarchy: str = "date_joined"
    filter_horizontal: Sequence[str] = ["user_permissions"]
    fieldsets: Sequence[tuple[str | None, dict[str, Sequence[str | Sequence[str]]]]] = (
        (None, {
            "fields": ("username", ("first_name", "last_name"), "is_active")
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
    add_fieldsets: Sequence[tuple[str | None, dict[str, Sequence[str | Sequence[str]]]]] = (
        (None, {
            "fields": (
                "username",
                ("password1", "password2"),
                ("first_name", "last_name")
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
    list_display: Sequence[str] = (
        "username",
        "first_name",
        "last_name",
        "is_staff",
        "is_active"
    )
    list_display_links: Sequence[str] = ("username",)
    list_editable: Sequence[str] = (
        "first_name",
        "last_name",
        "is_staff",
        "is_active"
    )
    list_filter: Sequence[admin.ListFilter | tuple[str, admin.ListFilter]] = (
        StaffListFilter,
        GroupListFilter,
        UserIsActiveListFilter,
        ("date_joined", DateTimeRangeFilter),
        ("last_login", DateTimeRangeFilter)
    )
    autocomplete_fields: Sequence[str] = ("groups",)
    readonly_fields: Sequence[str] = (
        "password",
        "display_date_joined",
        "display_last_login"
    )
    search_fields: Sequence[str] = ("username", "first_name", "last_name")
    search_help_text = "Search for a username, first name or last name"

    @admin.display(description="Date joined", ordering="date_joined")
    def display_date_joined(self, obj: User) -> str:
        """
            Returns the custom formatted string representation of the
            date_joined field, to be displayed on the admin page.
        """

        return obj.date_joined.strftime("%d %b %Y %I:%M:%S %p")

    @admin.display(description="Last login", ordering="last_login")
    def display_last_login(self, obj: User) -> str:
        """
            Returns the custom formatted string representation of the
            last_login field, to be displayed on the admin page.
        """

        return obj.last_login.strftime("%d %b %Y %I:%M:%S %p")

    def get_form(self, *args, **kwargs) -> Type[BaseModelForm]:
        """
            Return a Form class for use in the admin add view. This is used by
            add_view and change_view.

            Changes the labels on the form to remove unnecessary clutter.
        """

        kwargs.update(
            {
                "labels": {"password": "Hashed password string"},
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
