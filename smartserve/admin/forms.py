from typing import Any

from django import forms
from django.contrib.admin import widgets
from django.contrib.auth.forms import UserChangeForm as DjangoUserChangeForm
from django.forms import ModelForm as DjangoModelForm
from django.utils.translation import gettext_lazy as _

from smartserve.models import MenuItem, Restaurant, User


class UserChangeForm(DjangoUserChangeForm):
    restaurants = forms.ModelMultipleChoiceField(
        queryset=Restaurant.objects.all(),
        required=False,
        widget=widgets.FilteredSelectMultiple(
            verbose_name=_("Restaurants"),
            is_stacked=False
        ),
        help_text=_("The set of restaurants that this user is employed at. (Hold down “Control”, or “Command” on a Mac, to select more than one.)")
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
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


class RestaurantModelForm(DjangoModelForm):
    menu_items = forms.ModelMultipleChoiceField(
        queryset=MenuItem.objects.all(),
        required=False,
        widget=widgets.FilteredSelectMultiple(
            verbose_name=_("Menu Items"),
            is_stacked=False
        ),
        help_text=_("The set of menu items available at this restaurant. Hold down “Control”, or “Command” on a Mac, to select more than one.")
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields["menu_items"].initial = self.instance.menu_items.all()

    def save(self, commit: bool = True) -> Restaurant:
        restaurant: Restaurant = super().save(commit=False)

        if commit:
            restaurant.save()

        if restaurant.pk:
            restaurant.menu_items.set(self.cleaned_data["menu_items"])
            self.save_m2m()

        return restaurant
