from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.utils import timezone

from smartserve.models import Restaurant, Seat, Table, User
from smartserve.tests import utils
from smartserve.tests.utils import TestCase, TestRestaurantFactory, TestSeatFactory, TestTableFactory, TestUserFactory


class UserModelTests(TestCase):
    def test_employee_id_validate_regex(self):
        unicode_id: int
        for unicode_id in utils.UNICODE_IDS:
            if chr(unicode_id).isdecimal():
                continue

            invalid_employee_id: str = chr(unicode_id) * 6

            with self.subTest(invalid_employee_id=invalid_employee_id):
                with self.assertRaisesMessage(ValidationError, "Employee ID must be a 6 digit number"):
                    TestUserFactory.create(employee_id=invalid_employee_id)

    def test_employee_id_validate_min_length(self):
        for invalid_employee_id_length in range(1, 6):
            with self.subTest(invalid_employee_id_length=invalid_employee_id_length):
                with self.assertRaisesMessage(ValidationError, "Employee ID must be 6 digits"):
                    TestUserFactory.create(employee_id="9" * invalid_employee_id_length)

    def test_employee_id_validate_max_length(self):
        for invalid_employee_id_length in range(7, 12):
            with self.subTest(invalid_employee_id_length=invalid_employee_id_length):
                with self.assertRaisesMessage(ValidationError, f"Employee ID must be 6 digits"):
                    TestUserFactory.create(employee_id="9" * invalid_employee_id_length)

    def test_employee_id_auto_generated(self):
        self.assertTrue(
            bool(
                User.objects.create_user(
                    first_name=TestUserFactory.create_field_value("first_name"),
                    last_name=TestUserFactory.create_field_value("last_name")
                ).employee_id
            )
        )
        self.assertTrue(bool(TestUserFactory.create(employee_id="").employee_id))
        self.assertTrue(bool(TestUserFactory.create(employee_id=None).employee_id))

    def test_employee_id_validate_unique(self):
        non_unique_employee_id: str = TestUserFactory.create().employee_id

        with self.assertRaisesMessage(ValidationError, "user with that Employee ID already exists"):
            TestUserFactory.create(employee_id=non_unique_employee_id)

    def test_char_field_validate_required(self):
        char_field_name: str
        for char_field_name in ("first_name", "last_name"):
            with self.subTest(char_field_name=char_field_name):
                with self.assertRaisesMessage(ValidationError, "field cannot be null"):
                    TestUserFactory.create(**{char_field_name: None})

                with self.assertRaisesMessage(ValidationError, "field cannot be blank"):
                    TestUserFactory.create(**{char_field_name: ""})

    def test_date_joined_is_now(self):
        now: datetime = timezone.now()
        self.assertTrue((TestUserFactory.create().date_joined - now) < timedelta(microseconds=2))

    def test_str(self):
        user: User = TestUserFactory.create()
        self.assertIn(user.employee_id, str(user))
        self.assertIn(user.full_name, str(user))

    def test_superuser_becomes_staff(self):
        user: User = TestUserFactory.create()

        self.assertFalse(user.is_staff)

        user.update(is_superuser=True)
        user.refresh_from_db()

        self.assertTrue(user.is_staff)

    def test_full_name_validate_unique_per_restaurant(self):
        restaurant: Restaurant = TestRestaurantFactory.create()

        user_1: User = TestUserFactory.create()
        restaurant.employees.add(user_1)

        user_2: User = TestUserFactory.create()
        restaurant.employees.add(user_2)

        with self.assertRaisesMessage(ValidationError, "employee with that first & last name already exists"):
            user_2.update(first_name=user_1.first_name, last_name=user_1.last_name)

    def test_full_name_contains_first_name_and_last_name(self):
        user: User = TestUserFactory.create()

        self.assertIn(user.first_name, user.full_name)
        self.assertIn(user.last_name, user.full_name)

    def test_short_name_contains_first_name_or_last_name(self):
        user: User = TestUserFactory.create()

        self.assertTrue(user.first_name in user.short_name or user.last_name in user.short_name)


class RestaurantModelTests(TestCase):
    def test_name_validate_regex(self):
        invalid_names: set[str] = {
            f""" {TestRestaurantFactory.create_field_value("name")}""",
            f"""{TestRestaurantFactory.create_field_value("name")} """,
            f""" {TestRestaurantFactory.create_field_value("name")} """
        }

        unicode_id: int
        for unicode_id in utils.UNICODE_IDS:
            if chr(unicode_id).isalpha():
                continue

            invalid_names.add(chr(unicode_id) * 6)

        invalid_name: str
        for invalid_name in invalid_names:
            with self.subTest(invalid_name=invalid_name):
                with self.assertRaisesMessage(ValidationError, "Enter a valid value"):
                    TestRestaurantFactory.create(name=invalid_name)

    def test_name_validate_min_length(self):
        with self.assertRaisesMessage(ValidationError, "least 2 characters (it has 1"):
            TestRestaurantFactory.create(name=TestRestaurantFactory.create_field_value("name")[:1])

    def test_name_validate_max_length(self):
        for invalid_name_length in range(101, 105):
            with self.subTest(invalid_name_length=invalid_name_length):
                with self.assertRaisesMessage(ValidationError, f"most 100 characters (it has {invalid_name_length}"):
                    TestRestaurantFactory.create(
                        name=utils.duplicate_string_to_size(
                            TestRestaurantFactory.create_field_value("name"),
                            size=invalid_name_length
                        )
                    )

    def test_name_validate_required(self):
        with self.assertRaisesMessage(ValidationError, "field cannot be null"):
            TestRestaurantFactory.create(name=None)

        with self.assertRaisesMessage(ValidationError, "field cannot be blank"):
            TestRestaurantFactory.create(name="")

    def test_str(self):
        restaurant: Restaurant = TestRestaurantFactory.create()
        self.assertIn(restaurant.name, str(restaurant))


class TableModelTests(TestCase):
    def test_number_validate_required(self):
        with self.assertRaisesMessage(ValidationError, "field cannot be null"):
            TestTableFactory.create(number=None)

    def test_number_validate_min_value(self):
        with self.assertRaisesMessage(ValidationError, "greater than or equal to 1"):
            TestTableFactory.create(number=0)

    def test_restaurant_validate_required(self):
        with self.assertRaisesMessage(ValidationError, "field cannot be null"):
            TestTableFactory.create(restaurant=None)

    def test_true_number_without_container_table(self):
        table: Table = TestTableFactory.create()

        self.assertEqual(table.number, table.true_number)

    def test_true_number_with_container_table(self):
        container_table_number: int = TestTableFactory.create_field_value("number")
        table: Table = TestTableFactory.create(container_table__number=container_table_number)

        self.assertEqual(container_table_number, table.true_number)

    def test_true_number_with_double_container_table(self):
        container_table_number: int = TestTableFactory.create_field_value("number")
        table: Table = TestTableFactory.create(container_table__container_table__number=container_table_number)

        self.assertEqual(container_table_number, table.true_number)

    def test_seats_without_child_tables(self):
        table: Table = TestTableFactory.create()
        TestSeatFactory.create(table=table)
        TestSeatFactory.create(table=table)

        self.assertQuerysetEqual(
            Seat.objects.filter(pk__in=table._seats.all()),
            table.seats.all(),
            ordered=False
        )

        table.update(
            container_table=TestTableFactory.create(restaurant=table.restaurant)
        )
        TestSeatFactory.create(table=table.container_table)
        TestSeatFactory.create(table=table.container_table)

        self.assertQuerysetEqual(
            Seat.objects.filter(pk__in=table._seats.all()),
            table.seats.all(),
            ordered=False
        )

    def test_seats_with_child_tables_and_without_container_table(self):
        table: Table = TestTableFactory.create()
        sub_table: Table = TestTableFactory.create(container_table=table)

        self.assertQuerysetEqual(
            Seat.objects.filter(
                pk__in=table._seats.all() | sub_table._seats.all() | TestTableFactory.create(container_table=table)._seats.all() | TestTableFactory.create(container_table=sub_table)._seats.all()
            ),
            table.seats.all(),
            ordered=False
        )

    def test_seats_with_child_tables_and_with_container_table(self):  # TODO
        raise NotImplementedError
