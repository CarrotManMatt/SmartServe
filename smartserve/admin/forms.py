from django import forms
from django.contrib.admin import widgets
from django.contrib.auth.forms import UserChangeForm
from django.utils.translation import gettext_lazy as _

from smartserve.models import Restaurant, User


class Custom_User_Admin_Form(UserChangeForm):
    restaurants = forms.ModelMultipleChoiceField(
        queryset=Restaurant.objects.all(),
        required=False,
        widget=widgets.FilteredSelectMultiple(
            verbose_name=_("Restaurants"),
            is_stacked=False
        ),
        help_text=_("The set of restaurants that this user is employed at. (Hold down “Control”, or “Command” on a Mac, to select more than one.)")
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields["restaurants"].initial = self.instance.restaurants.all()

    def save(self, commit: bool = True) -> User:
        user: User = super().save(commit=False)

        if commit:
            user.save()

        if user.pk:
            user.restaurants.set(self.cleaned_data["restaurants"])  # type: ignore
            self.save_m2m()

        return user
