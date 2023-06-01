"""
    Root URL conf for SmartServe project.
"""

import django.urls
from django.contrib import admin
from django.urls import URLPattern, URLResolver
from knox.views import LogoutAllView, LogoutView  # type: ignore

from .views import Admin_Docs_Redirect_View, LoginView

# noinspection SpellCheckingInspection
urlpatterns: list[URLResolver | URLPattern] = [
    django.urls.path(
        r"admin/doc/",
        django.urls.include("django.contrib.admindocs.urls")
    ),
    django.urls.path(r"admin/docs/", Admin_Docs_Redirect_View.as_view()),
    django.urls.path(
        r"admin/docs/<path:subpath>",
        Admin_Docs_Redirect_View.as_view()
    ),
    django.urls.path(r"admin/", admin.site.urls),
    django.urls.path(
        r"api/auth/login/",
        LoginView.as_view(),
        name="knox_login"
    ),
    django.urls.path(
        r"api/auth/logout/",
        LogoutView.as_view(),
        name="knox_logout"
    ),
    django.urls.path(
        r"api/auth/logoutall/",
        LogoutAllView.as_view(),
        name="knox_logoutall"
    ),
    django.urls.path("api/", django.urls.include("smartserve.urls"))
]