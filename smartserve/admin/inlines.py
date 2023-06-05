from typing import Sequence

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from knox.models import AuthToken

from smartserve.models import Table


class Auth_Tokens_Inline(admin.StackedInline):
    classes = ["collapse"]
    extra = 0
    model = AuthToken


class Tables_Inline(admin.TabularInline):
    extra = 0
    model = Table
    verbose_name_plural = _("Tables (including Sub-Tables)")

    def get_queryset(self, request: HttpRequest) -> QuerySet[Table]:
        queryset: QuerySet[Table] = self.model.objects.all_with_sub_tables()

        ordering: Sequence[str] = self.get_ordering(request)
        if ordering:
            queryset = queryset.order_by(*ordering)

        if not self.has_view_or_change_permission(request):
            queryset = queryset.none()

        return queryset
