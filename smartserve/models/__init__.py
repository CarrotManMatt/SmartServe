from django.apps import apps
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import AbstractUser, Permission, UserManager
from django.db import models

from smartserve.models.utils import Attribute_Deleter, Custom_Base_Model


class Custom_User_Manager(UserManager):
    normalize_email = Attribute_Deleter(object_name="Custom_User_Manager", attribute_name="normalize_email")  # type: ignore

    use_in_migrations: bool = True

    def _create_user(self, username: str, password: str | None = None, **extra_fields) -> "User":
        if not username:
            raise ValueError("The given username must be set")

        # noinspection PyProtectedMember
        GlobalUserModel: AbstractBaseUser = apps.get_model(  # type: ignore
            self.model._meta.app_label, self.model._meta.object_name
        )
        user: "User" = self.model(  # type: ignore
            username=GlobalUserModel.normalize_username(username),
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username: str, password: str | None = None, **extra_fields) -> "User":  # type: ignore
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        return self._create_user(username, password, **extra_fields)

    def create_superuser(self, username: str, password: str | None = None, **extra_fields) -> "User":  # type: ignore
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(username, password, **extra_fields)


class User(Custom_Base_Model, AbstractUser):
    email = Attribute_Deleter(object_name="User", attribute_name="email")  # type: ignore
    EMAIL_FIELD = Attribute_Deleter(object_name="User", attribute_name="EMAIL_FIELD")  # type: ignore
    email_user = Attribute_Deleter(object_name="User", attribute_name="email_user")  # type: ignore
    get_email_field_name = Attribute_Deleter(object_name="User", attribute_name="get_email_field_name")  # type: ignore

    REQUIRED_FIELDS: list[str] = []
    objects: models.Manager = Custom_User_Manager()  # type: ignore

    class Meta:
        verbose_name: str = "User"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._meta.get_field("password").error_messages = {
            "null": "Password is a required field.",
            "blank": "Password is a required field."
        }

    # TODO: Test if stringify is good
    # TODO: Test if superuser automatically becomes staff

    def clean(self) -> None:
        setattr(
            self,
            self.USERNAME_FIELD,
            self.normalize_username(self.get_username())
        )

    def get_absolute_url(self) -> str:  # TODO
        raise NotImplementedError
