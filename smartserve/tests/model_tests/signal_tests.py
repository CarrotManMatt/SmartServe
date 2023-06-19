from django.db import IntegrityError, transaction

from smartserve.models import Restaurant, User
from smartserve.tests.utils import TestCase, TestRestaurantFactory, TestUserFactory


class UserAddedToRestaurantSignalTests(TestCase):
    def test_non_unique_user_not_added_to_restaurant(self) -> None:
        restaurant: Restaurant = TestRestaurantFactory.create()

        user_1: User = TestUserFactory.create()
        user_2: User = TestUserFactory.create(first_name=user_1.first_name, last_name=user_1.last_name)
        restaurant.employees.add(user_1)

        with transaction.atomic(), self.assertRaisesMessage(IntegrityError, "UNIQUE constraint failed"):
            restaurant.employees.add(user_2)

        self.assertNotIn(user_2, restaurant.employees.all())

    def test_non_unique_user_restaurant_not_added(self) -> None:
        restaurant: Restaurant = TestRestaurantFactory.create()

        user_1: User = TestUserFactory.create()
        user_2: User = TestUserFactory.create(first_name=user_1.first_name, last_name=user_1.last_name)
        restaurant.employees.add(user_1)

        with transaction.atomic(), self.assertRaisesMessage(IntegrityError, "UNIQUE constraint failed"):
            user_2.restaurants.add(restaurant)  # type: ignore

        self.assertNotIn(restaurant, user_2.restaurants.all())
