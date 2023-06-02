from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import Permission, PermissionsMixin, UserManager
from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from smartserve.models.utils import Attribute_Deleter, Custom_Base_Model
from . import utils


class Custom_User_Manager(UserManager):
    normalize_email = Attribute_Deleter(object_name="Custom_User_Manager", attribute_name="normalize_email")  # type: ignore

    use_in_migrations: bool = True

    def _create_user(self, password: str | None = None, **extra_fields) -> "User":
        user: "User" = self.model(**extra_fields)  # type: ignore
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, password: str | None = None, **extra_fields) -> "User":  # type: ignore
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        return self._create_user(password, **extra_fields)

    def create_superuser(self, password: str | None = None, **extra_fields) -> "User":  # type: ignore
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(password, **extra_fields)


class User(Custom_Base_Model, AbstractBaseUser, PermissionsMixin):
    get_email_field_name = Attribute_Deleter(object_name="User", attribute_name="get_email_field_name")  # type: ignore
    normalize_username = Attribute_Deleter(object_name="User", attribute_name="normalize_username")  # type: ignore

    employee_id = models.CharField(
        _("Employee ID"),
        unique=True,
        max_length=6,
        validators=[RegexValidator(r"^\d+\Z"), MinLengthValidator(6)],
        default=utils.generate_employee_id,
        error_messages={
            "unique": _("A user with that ID already exists."),
        },
        blank=True
    )
    first_name = models.CharField(_("First Name"), max_length=75)
    last_name = models.CharField(_("Last Name"), max_length=75)
    is_staff = models.BooleanField(
        _("Is Admin?"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        _("Is Active?"),
        default=True,
        help_text=_("Designates whether this user should be treated as active. Unselect this instead of deleting accounts."),
    )
    date_joined = models.DateTimeField(_("Date Joined"), default=timezone.now)

    objects = Custom_User_Manager()

    USERNAME_FIELD: str = "employee_id"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = _("User")
        abstract = False

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._meta.get_field("password").error_messages = {
            "null": _("Password is a required field."),
            "blank": _("Password is a required field.")
        }
        self._meta.get_field("is_superuser").verbose_name = _("Is Superuser?")

    def __str__(self) -> str:
        return self.full_name

    def clean(self) -> None:
        if self.is_superuser:
            self.is_staff = True

        if not self.employee_id:
            self.employee_id = utils.generate_employee_id()

    @property
    def full_name(self) -> str:
        """ Return the first_name plus the last_name, with a space in between. """

        return f"{self.first_name} {self.last_name}"

    @property
    def short_name(self) -> str:
        """ Return the short name for the user. """

        return self.first_name

    def get_absolute_url(self) -> str:  # TODO
        raise NotImplementedError
