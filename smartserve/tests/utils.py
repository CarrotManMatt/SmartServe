import abc
import copy
import itertools
import json
from contextlib import AbstractContextManager
from typing import Any, Iterable, Iterator

from django.conf import settings
from django.contrib import auth
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import IntegrityError
from django.test import TestCase as DjangoTestCase

from smartserve.exceptions import NotEnoughTestDataError
from smartserve.models import Restaurant, Seat, Table, User

UNICODE_IDS: Iterable[int] = itertools.chain(
    range(32, 128),
    range(160, 256),
    range(321, 329),
    range(330, 370),
    range(372, 384),
    (390, 398, 412),
    range(592, 595),
    (596,),
    range(600, 602),
    range(603, 605),
    range(606, 608),
    range(609, 614),
    (616, 618, 620),
    range(622, 625),
    range(628, 634),
    (641, 647),
    range(652, 655),
    (670,),
    range(913, 930),
    range(931, 938),
    range(945, 970),
    range(1040, 1104),
    range(7424, 7467),
    (7838,),
    range(7922, 7926),
    range(7928, 7930),
    range(8208, 8232),
    range(8240, 8278),
    (8279,),
    range(8304, 8306),
    range(8308, 8335),
    range(8352, 8378),
    range(8448, 8505),
    range(8513, 8522),
    (8523, 8526),
    range(8528, 8576),
    (8580,),
    range(8592, 8946),
    range(8960, 8972),
    range(8976, 8988),
    range(8992, 9001),
    range(9003, 9005),
    range(9115, 9134),
    range(9166, 9168),
    range(9178, 9180),
    range(9200, 9204),
    range(9250, 9252),
    range(9472, 9840),
    range(9842, 9862),
    range(9872, 9917),
    range(9920, 9924),
    (9954,),
    range(9956, 9984),
    range(9985, 10088),
    (10132,),
    range(10136, 10160),
    range(10161, 10175),
    range(10224, 10240),
    range(10496, 10578),
    range(11008, 11035),
    range(11360, 11362),
    (11363,),
    range(11365, 11367),
    (11373,),
    range(11375, 11377),
    range(11810, 11814),
    (11822,),
    range(12291, 12293),
    range(64256, 64263),
    range(64830, 64832),
    (65020,),
    range(65040, 65050),
    range(65072, 65095),
    range(65097, 65107),
    range(65108, 65127),
    range(65128, 65132),
    (65279,),
    range(65281, 65377),
    range(65504, 65511)
)


def duplicate_string_to_size(string: str, size: int, strip: bool = False) -> str:
    if len(string) >= size:
        shortened_string: str = string[:size]

    else:
        partial_string: str = string * (size // len(string))
        shortened_string = partial_string + string[:size - len(partial_string)]

    if strip:
        stripped_shortened_string: str = shortened_string.strip()
        if stripped_shortened_string != shortened_string:
            shortened_string = duplicate_string_to_size(stripped_shortened_string, size)

    return shortened_string


TEST_DATA: dict[str, dict[str, Iterable[str]]] = {}
if settings.TEST_DATA_JSON_FILE_PATH:
    with open(settings.TEST_DATA_JSON_FILE_PATH, "r") as test_data_json_file:
        TEST_DATA = json.load(test_data_json_file)


def get_field_test_data(model_name: str, field_name: str) -> Iterable[str]:
    """
        Returns the set of test data values for the given model_name and
        field_name, from the test data JSON file.
    """

    if not TEST_DATA:
        raise ImproperlyConfigured(f"TEST_DATA_JSON_FILE_PATH cannot be empty when running tests.")

    return set(TEST_DATA[model_name][field_name])


class TestCase(DjangoTestCase):
    def setUp(self) -> None:
        Factory: type[BaseTestDataFactory]
        for Factory in (TestUserFactory, TestRestaurantFactory, TestTableFactory, TestSeatFactory):
            Factory.test_data_iterators = copy.deepcopy(Factory.ORIGINAL_TEST_DATA_ITERATORS)

    def subTest(self, msg: str | None = None, **params) -> AbstractContextManager[None]:
        self.setUp()

        return super().subTest(msg, **params)


class BaseTestDataFactory(abc.ABC):
    """
        Helper class to provide functions that create test object instances of
        any model within the smartserve app.
    """

    MODEL: type
    ORIGINAL_TEST_DATA_ITERATORS: dict[str, Iterator[Any]]
    test_data_iterators: dict[str, Iterator[Any]]

    @classmethod
    def create(cls, *, save: bool = True, **kwargs):
        """
            Helper function that creates & returns a test object instance, with
            additional options for its attributes provided in kwargs. The save
            argument declares whether the object instance should be saved to
            the database or not.
        """

        previous_test_data_iterators: dict[str, Iterator[Any]] = copy.deepcopy(cls.test_data_iterators)

        for field_name in cls.test_data_iterators.keys():
            kwargs.setdefault(field_name, cls.create_field_value(field_name))

        try:
            if save:
                if cls.MODEL == auth.get_user_model():
                    return auth.get_user_model().objects.create_user(**kwargs)
                else:
                    return cls.MODEL.objects.create(**kwargs)  # type: ignore
            else:
                # noinspection PyCallingNonCallable
                return cls.MODEL(**kwargs)

        except (ValidationError, IntegrityError):
            cls.test_data_iterators = previous_test_data_iterators
            raise

    @classmethod
    def create_field_value(cls, field_name: str) -> Any:
        """
            Helper function to return a new arbitrary value for the given field
            name.
        """

        try:
            return next(cls.test_data_iterators[field_name])
        except StopIteration as test_data_iterator_error:
            raise NotEnoughTestDataError(field_name=field_name) from test_data_iterator_error


class TestUserFactory(BaseTestDataFactory):
    """
        Helper class to provide functions that create test data for
        :model:`smartserve.user` object instances.
    """

    MODEL: type = User
    # noinspection PyProtectedMember
    ORIGINAL_TEST_DATA_ITERATORS: dict[str, Iterator[Any]] = {
        "first_name": iter(get_field_test_data(MODEL._meta.model_name or "user", "first_name")),
        "last_name": iter(get_field_test_data(MODEL._meta.model_name or "user", "last_name"))
    }


class TestRestaurantFactory(BaseTestDataFactory):
    """
        Helper class to provide functions that create test data for
        :model:`smartserve.restaurant` object instances.
    """

    MODEL: type = Restaurant
    # noinspection PyProtectedMember
    ORIGINAL_TEST_DATA_ITERATORS: dict[str, Iterator[Any]] = {
        "name": iter(get_field_test_data(MODEL._meta.model_name, "name"))
    }


class TestTableFactory(BaseTestDataFactory):
    """
        Helper class to provide functions that create test data for
        :model:`smartserve.table` object instances.
    """

    MODEL: type = Table
    ORIGINAL_TEST_DATA_ITERATORS: dict[str, Iterator[Any]] = {"number": itertools.count(1)}

    @classmethod
    def create(cls, *, save=True, **kwargs):
        restaurant_kwargs: dict[str, Any] = {}
        for restaurant_field_name in {restaurant_field_name for restaurant_field_name in kwargs.keys() if restaurant_field_name.startswith("restaurant__")}:
            restaurant_kwargs[restaurant_field_name.removeprefix("restaurant__")] = kwargs.pop(restaurant_field_name)

        if "restaurant" in kwargs and restaurant_kwargs:
            raise ValueError("Invalid arguments supplied: choose one of \"restaurant\" instance or \"restaurant__\" attributes.")

        if "restaurant" not in kwargs:
            if "container_table" in kwargs:
                kwargs.setdefault("restaurant", kwargs["container_table"].restaurant)
            else:
                kwargs.setdefault("restaurant", TestRestaurantFactory.create(**restaurant_kwargs))

        container_table_kwargs: dict[str, Any] = {}
        for container_table_field_name in {container_table_field_name for container_table_field_name in kwargs.keys() if container_table_field_name.startswith("container_table__")}:
            container_table_kwargs[container_table_field_name.removeprefix("container_table__")] = kwargs.pop(container_table_field_name)

        if "container_table" in kwargs and container_table_kwargs:
            raise ValueError("Invalid arguments supplied: choose one of \"container_table\" instance or \"container_table__\" attributes.")

        table: Table = super().create(save=save, **kwargs)

        if "container_table" not in kwargs and container_table_kwargs:
            container_table_kwargs.setdefault("restaurant", table.restaurant)
            table.update(container_table=TestTableFactory.create(**container_table_kwargs))

        return table


class TestSeatFactory(BaseTestDataFactory):
    """
        Helper class to provide functions that create test data for
        :model:`smartserve.seat` object instances.
    """

    MODEL: type = Seat
    ORIGINAL_TEST_DATA_ITERATORS: dict[str, Iterator[Any]] = {"location_index": itertools.count(1)}

    @classmethod
    def create(cls, *, save=True, **kwargs: Any):
        table_kwargs: dict[str, Any] = {}
        for table_field_name in {table_field_name for table_field_name in kwargs.keys() if table_field_name.startswith("table__")}:
            table_kwargs[table_field_name.removeprefix("table__")] = kwargs.pop(table_field_name)

        if "table" in kwargs and table_kwargs:
            raise ValueError("Invalid arguments supplied: choose one of \"table\" instance or \"table__\" attributes.")

        if "table" not in kwargs:
            kwargs.setdefault("table", TestTableFactory.create(**table_kwargs))

        return super().create(save=save, **kwargs)
