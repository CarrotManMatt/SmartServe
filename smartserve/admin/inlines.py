from django.contrib import admin
from knox.models import AuthToken


class Auth_Tokens_Inline(admin.StackedInline):
    classes = ["collapse"]
    extra = 0
    fk_name = "user"
    model = AuthToken
