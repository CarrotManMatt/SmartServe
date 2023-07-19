from typing import Any, TYPE_CHECKING

from django.contrib.auth.models import UserManager as DjangoUserManager

from .utils import AttributeDeleter

if TYPE_CHECKING:
    from smartserve.models import User


class UserManager(DjangoUserManager):
    normalize_email = AttributeDeleter(object_name="UserManager", attribute_name="normalize_email")  # type: ignore

    use_in_migrations: bool = True

    def _create_user(self, password: str | None = None, **extra_fields: Any) -> "User":
        user: "User" = self.model(**extra_fields)  # type: ignore
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, password: str | None = None, **extra_fields: Any) -> "User":  # type: ignore
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        return self._create_user(password, **extra_fields)

    def create_superuser(self, password: str | None = None, **extra_fields: Any) -> "User":  # type: ignore
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(password, **extra_fields)
