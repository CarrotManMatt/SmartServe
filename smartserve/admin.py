"""
    Admin configurations for models in smartserve app.
"""

from typing import Type

from django.contrib import admin, auth
from django.contrib.auth.admin import UserAdmin
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from rangefilter.filters import DateTimeRangeFilterBuilder

from admin_inlines import Auth_Tokens_Inline
from smartserve.admin_filters import Group_List_Filter, Staff_List_Filter, User_Is_Active_List_Filter
from smartserve.models import User

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

    date_hierarchy = "date_joined"
    filter_horizontal = ("user_permissions",)
    fieldsets = (
        (None, {
            "fields": ("employee_id", ("first_name", "last_name"), "is_active")
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

        if not obj.last_login:
            return ""

        return obj.last_login.strftime("%d %b %Y %I:%M:%S %p")

    def get_form(self, *args, **kwargs) -> Type[ModelForm]:
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
