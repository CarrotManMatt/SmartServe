"""
    Views for direct use in core app.
"""

from typing import Any, Callable, Sequence, Union

from django import urls as django_urls
from django.contrib import auth
from django.views.generic import RedirectView
from knox.views import LoginView as KnoxLoginView
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.permissions import AllowAny, BasePermission
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer


class AdminDocsRedirectView(RedirectView):
    """
        Helper redirect view for the docs/ url to doc/ (with any included
        subpath).
    """

    _get_redirect_url_types = Union[str, Sequence, dict[str, Any], None, Callable]

    def get_redirect_url(self, *args: _get_redirect_url_types, **kwargs: _get_redirect_url_types) -> str:
        """
            Return the URL redirect to. Keyword arguments from the URL pattern
            match generating the redirect request are provided as kwargs to
            this method. Also adds a possible subpath to the end of the
            redirected URL.
        """

        subpath: str = ""
        if "subpath" in self.kwargs:
            subpath = self.kwargs.pop("subpath")
            kwargs.pop("subpath")

        # noinspection SpellCheckingInspection
        url: str = django_urls.reverse("django-admindocs-docroot", args=args, kwargs=kwargs) + subpath

        url_args: str = self.request.META.get("QUERY_STRING", "")
        if url_args and self.query_string:
            url = f"{url}?{url_args}"

        return url


class LoginView(KnoxLoginView):
    """
        Customised login view to accept all users.

        (Login is done by POST request rather than authorisation headers.)
    """

    permission_classes: Sequence[type[BasePermission]] = [AllowAny]

    def post(self, request: Request, format: str | None = None) -> Response:
        """
            Attempt to log user in by generating an API token from the given
            POST request data.
        """

        serializer: BaseSerializer = AuthTokenSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        auth.login(request, serializer.validated_data["user"])

        return super(LoginView, self).post(request)  # type: ignore
