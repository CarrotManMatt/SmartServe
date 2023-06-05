from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import UserManager
from django.db.models import Manager, QuerySet

from .utils import Attribute_Deleter


class Custom_User_Manager(UserManager):
    normalize_email = Attribute_Deleter(object_name="Custom_User_Manager", attribute_name="normalize_email")  # type: ignore

    use_in_migrations: bool = True

    def _create_user(self, password: str | None = None, **extra_fields) -> AbstractBaseUser:
        user: AbstractBaseUser = self.model(**extra_fields)  # type: ignore
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, password: str | None = None, **extra_fields) -> AbstractBaseUser:  # type: ignore
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        return self._create_user(password, **extra_fields)

    def create_superuser(self, password: str | None = None, **extra_fields) -> AbstractBaseUser:  # type: ignore
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(password, **extra_fields)


class Table_Manager(Manager):
    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter(container_table__isnull=True)

    def all_with_sub_tables(self) -> QuerySet:
        return super().get_queryset()
