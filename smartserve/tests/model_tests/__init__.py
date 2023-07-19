from datetime import datetime, timedelta
from typing import Any, Iterable

from django.core.exceptions import ValidationError
from django.utils import timezone

from smartserve.models import Booking, Restaurant, Seat, Table, User
from smartserve.tests import utils
from smartserve.tests.utils import TestBookingFactory, TestCase, TestRestaurantFactory, TestSeatBookingFactory, TestSeatFactory, TestTableFactory, TestUserFactory


class UserModelTests(TestCase):
    def test_employee_id_validate_regex(self) -> None:
        unicode_id: int
        for unicode_id in utils.UNICODE_IDS:
            if chr(unicode_id).isdecimal():
                continue

            invalid_employee_id: str = chr(unicode_id) * 6

            with self.subTest("Invalid unicode employee_id provided", invalid_employee_id=invalid_employee_id):
                with self.assertRaisesMessage(ValidationError, "Employee ID must be a 6 digit number"):
                    TestUserFactory.create(employee_id=invalid_employee_id)

    def test_employee_id_validate_min_length(self) -> None:
        invalid_employee_id_length: int
        for invalid_employee_id_length in range(1, 6):
            with self.subTest("Too short employee_id provided", invalid_employee_id_length=invalid_employee_id_length):
                with self.assertRaisesMessage(ValidationError, "Employee ID must be 6 digits"):
                    TestUserFactory.create(employee_id="9" * invalid_employee_id_length)

    def test_employee_id_validate_correct_length(self) -> None:
        try:
            TestUserFactory.create(employee_id="9" * 6)
        except ValidationError as validate_error:
            self.fail(f"ValidationError raised: {validate_error}")

    def test_employee_id_validate_max_length(self) -> None:
        for invalid_employee_id_length in range(7, 12):
            with self.subTest("Too long employee_id provided", invalid_employee_id_length=invalid_employee_id_length):
                with self.assertRaisesMessage(ValidationError, f"Employee ID must be 6 digits"):
                    TestUserFactory.create(employee_id="9" * invalid_employee_id_length)

    def test_employee_id_auto_generated(self) -> None:
        with self.subTest("No employee_id provided"):
            self.assertTrue(
                bool(
                    User.objects.create_user(
                        first_name=TestUserFactory.create_field_value("first_name"), last_name=TestUserFactory.create_field_value("last_name")
                    ).employee_id
                )
            )

        employee_id: Any
        for employee_id in ("", None):
            with self.subTest("Empty employee_id provided", employee_id=employee_id):
                self.assertTrue(bool(TestUserFactory.create(employee_id=employee_id).employee_id))

    def test_employee_id_validate_unique(self) -> None:
        non_unique_employee_id: str = TestUserFactory.create().employee_id

        with self.assertRaisesMessage(ValidationError, "user with that Employee ID already exists"):
            TestUserFactory.create(employee_id=non_unique_employee_id)

    def test_char_field_validate_required(self) -> None:
        char_field_name: str
        for char_field_name in ("first_name", "last_name"):
            with self.subTest("Null value provided", char_field_name=char_field_name):
                with self.assertRaisesMessage(ValidationError, "field cannot be null"):
                    TestUserFactory.create(**{char_field_name: None})  # type: ignore

            with self.subTest("Blank value provided", char_field_name=char_field_name):
                with self.assertRaisesMessage(ValidationError, "field cannot be blank"):
                    TestUserFactory.create(**{char_field_name: ""})  # type: ignore

    def test_date_joined_is_now(self) -> None:
        now: datetime = timezone.now()

        self.assertTrue((TestUserFactory.create().date_joined - now) < timedelta(seconds=1))

    def test_str(self) -> None:
        user: User = TestUserFactory.create()

        self.assertIn(user.employee_id, str(user))
        self.assertIn(user.full_name, str(user))

    def test_superuser_becomes_staff(self) -> None:
        user: User = TestUserFactory.create()

        self.assertFalse(user.is_staff)

        user.update(is_superuser=True)
        user.refresh_from_db()

        self.assertTrue(user.is_staff)

    def test_full_name_validate_unique_per_restaurant(self) -> None:
        restaurant: Restaurant = TestRestaurantFactory.create()

        user_1: User = TestUserFactory.create()
        restaurant.employees.add(user_1)

        user_2: User = TestUserFactory.create()
        restaurant.employees.add(user_2)

        with self.assertRaisesMessage(ValidationError, "employee with that first & last name already exists"):
            user_2.update(first_name=user_1.first_name, last_name=user_1.last_name)

    def test_full_name_contains_first_name_and_last_name(self) -> None:
        user: User = TestUserFactory.create()

        self.assertIn(user.first_name, user.full_name)
        self.assertIn(user.last_name, user.full_name)

    def test_short_name_contains_first_name_or_last_name(self) -> None:
        user: User = TestUserFactory.create()

        self.assertTrue(user.first_name in user.short_name or user.last_name in user.short_name)


class RestaurantModelTests(TestCase):
    def test_name_validate_regex(self) -> None:
        partial_invalid_name: str = TestRestaurantFactory.create_field_value("name")
        invalid_names: set[str] = {f" {partial_invalid_name}", f"{partial_invalid_name} ", f" {partial_invalid_name} "}

        unicode_id: int
        for unicode_id in utils.UNICODE_IDS:
            if chr(unicode_id).isalpha():
                continue

            invalid_names.add(chr(unicode_id) * 6)

        invalid_name: str
        for invalid_name in invalid_names:
            with self.subTest("Invalid unicode name provided", invalid_name=invalid_name):
                with self.assertRaisesMessage(ValidationError, "Enter a valid value"):
                    TestRestaurantFactory.create(name=invalid_name)

    def test_name_validate_min_length(self) -> None:
        with self.assertRaisesMessage(ValidationError, "least 2 characters (it has 1"):
            TestRestaurantFactory.create(name=TestRestaurantFactory.create_field_value("name")[:1])

    def test_name_validate_correct_length(self) -> None:
        valid_name_length: int
        for valid_name_length in range(2, 101):
            with self.subTest("Valid length name provided", valid_name_length=valid_name_length):
                try:
                    TestRestaurantFactory.create(
                        name=utils.duplicate_string_to_size(
                            TestRestaurantFactory.create_field_value("name"), size=valid_name_length, strip=True
                        )
                    )
                except ValidationError as validate_error:
                    self.fail(f"ValidationError raised: {validate_error}")

    def test_name_validate_max_length(self) -> None:
        invalid_name_length: int
        for invalid_name_length in range(101, 105):
            with self.subTest("Too long name provided", invalid_name_length=invalid_name_length):
                with self.assertRaisesMessage(ValidationError, f"most 100 characters (it has {invalid_name_length}"):
                    TestRestaurantFactory.create(
                        name=utils.duplicate_string_to_size(
                            TestRestaurantFactory.create_field_value("name"), size=invalid_name_length, strip=True
                        )
                    )

    def test_name_validate_required(self) -> None:
        with self.assertRaisesMessage(ValidationError, "field cannot be null"):
            TestRestaurantFactory.create(name=None)

        with self.assertRaisesMessage(ValidationError, "field cannot be blank"):
            TestRestaurantFactory.create(name="")

    def test_str(self) -> None:
        restaurant: Restaurant = TestRestaurantFactory.create()

        self.assertIn(restaurant.name, str(restaurant))


class TableModelTests(TestCase):
    def test_number_validate_required(self) -> None:
        with self.assertRaisesMessage(ValidationError, "field cannot be null"):
            TestTableFactory.create(number=None)

    def test_number_validate_min_value(self) -> None:
        with self.assertRaisesMessage(ValidationError, "greater than or equal to 1"):
            TestTableFactory.create(number=0)

    def test_number_unique_per_restaurant(self) -> None:
        table: Table = TestTableFactory.create()

        with self.assertRaisesMessage(ValidationError, "this Number and Restaurant already exists"):
            TestTableFactory.create(
                number=table.number,
                restaurant=table.restaurant
            )

        try:
            TestTableFactory.create(
                number=table.number,
                restaurant=TestRestaurantFactory.create()
            )
        except ValidationError as validate_error:
            self.fail(f"ValidationError raised: {validate_error}")

        try:
            TestTableFactory.create(
                number=TestTableFactory.create_field_value("number"),
                restaurant=table.restaurant
            )
        except ValidationError as validate_error:
            self.fail(f"ValidationError raised: {validate_error}")

    def test_restaurant_validate_required(self) -> None:
        with self.assertRaisesMessage(ValidationError, "field cannot be null"):
            TestTableFactory.create(restaurant=None)

    def test_true_number_without_container_table(self) -> None:
        table: Table = TestTableFactory.create()

        self.assertEqual(table.number, table.true_number)

    def test_true_number_with_container_table(self) -> None:
        container_table_number: int = TestTableFactory.create_field_value("number")
        table: Table = TestTableFactory.create(container_table__number=container_table_number)

        self.assertEqual(container_table_number, table.true_number)

    def test_true_number_with_double_container_table(self) -> None:
        container_table_number: int = TestTableFactory.create_field_value("number")
        table: Table = TestTableFactory.create(container_table__container_table__number=container_table_number)

        self.assertEqual(container_table_number, table.true_number)

    def test_seats_without_child_tables(self) -> None:
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

    def test_seats_with_child_tables_and_without_container_table(self) -> None:
        table: Table = TestTableFactory.create()
        TestSeatFactory.create(table=table)
        TestSeatFactory.create(table=table)

        sub_table: Table = TestTableFactory.create(container_table=table)
        TestSeatFactory.create(table=sub_table)
        TestSeatFactory.create(table=sub_table)

        self.assertQuerysetEqual(
            Seat.objects.filter(
                pk__in=table._seats.all() | sub_table._seats.all() | TestTableFactory.create(container_table=table)._seats.all() | TestTableFactory.create(container_table=sub_table)._seats.all()
            ),
            table.seats.all(),
            ordered=False
        )

    def test_seats_with_child_tables_and_with_container_table(self) -> None:
        table: Table = TestTableFactory.create(container_table=TestTableFactory.create())
        TestSeatFactory.create(table=table)
        TestSeatFactory.create(table=table)

        TestSeatFactory.create(table=table.container_table)

        sub_table: Table = TestTableFactory.create(container_table=table)
        TestSeatFactory.create(table=sub_table)
        TestSeatFactory.create(table=sub_table)

        self.assertQuerysetEqual(
            table._seats.all(),
            table.seats.all(),
            ordered=False
        )

    def test_seats_without_pk(self) -> None:
        with self.assertRaisesMessage(ValueError, "'Table' instance needs to have a primary key"):
            TestTableFactory.create(save=False).seats.all()

    def test_bookings_with_pk(self) -> None:
        table: Table = TestTableFactory.create()

        booking_pks: set[int] = {
            TestSeatBookingFactory.create(seat__table=table).pk,
            TestSeatBookingFactory.create(seat__table=table).pk,
            TestSeatBookingFactory.create(seat__table=table).pk
        }

        TestSeatBookingFactory.create()
        TestSeatBookingFactory.create()

        self.assertQuerysetEqual(
            Booking.objects.filter(pk__in=booking_pks),
            table.bookings.all(),
            ordered=False
        )

    def test_bookings_without_pk(self) -> None:
        with self.assertRaisesMessage(ValueError, "'Table' instance needs to have a primary key"):
            TestTableFactory.create(save=False).bookings.all()

    def test_str(self) -> None:
        table: Table = TestTableFactory.create()

        self.assertIn(str(table.number), str(table))

    def test_container_table_validate_not_self(self) -> None:
        table: Table = TestTableFactory.create()

        with self.assertRaisesMessage(ValidationError, "parent container table cannot be this own table"):
            table.update(container_table=table)

    def test_container_table_validate_restaurant_is_same(self) -> None:
        table: Table = TestTableFactory.create()

        with self.assertRaisesMessage(ValidationError, "same restaurant"):
            table.update(
                container_table=TestTableFactory.create(
                    restaurant=TestRestaurantFactory.create()
                )
            )

    def test_container_table_validate_not_in_sub_tables(self) -> None:
        table: Table = TestTableFactory.create()

        sub_table: Table = TestTableFactory.create(container_table=table)
        invalid_container_tables: Iterable[Table] = (sub_table, TestTableFactory.create(container_table=sub_table))

        invalid_container_table: Table
        for invalid_container_table in invalid_container_tables:
            with self.subTest("Invalid container_table provided", invalid_container_table=invalid_container_table):
                with self.assertRaisesMessage(ValidationError, "parent container table cannot be a sub-table"):
                    table.update(container_table=invalid_container_table)

    def test_create_booking(self) -> None:
        start_end_pair: tuple[datetime, datetime] = TestBookingFactory.create_field_value("start_end_pair")
        table: Table = TestTableFactory.create()
        TestSeatFactory.create(table=table)
        TestSeatFactory.create(table=table)

        booking: Booking = table.create_booking(start_end_pair[0], start_end_pair[1])

        self.assertIsInstance(booking, Booking)
        self.assertEqual(start_end_pair[0], booking.start)
        self.assertEqual(start_end_pair[1], booking.end)
        self.assertQuerysetEqual(
            Seat.objects.filter(pk__in=booking.seat_bookings.values_list("pk", flat=True)),
            table.seats.all(),
            ordered=False
        )


class SeatModelTests(TestCase):
    def test_table_validate_required(self) -> None:
        with self.assertRaisesMessage(ValidationError, "field cannot be null"):
            TestSeatFactory.create(table=None)

    def test_location_index_validate_required(self) -> None:
        with self.assertRaisesMessage(ValidationError, "field cannot be null"):
            TestSeatFactory.create(location_index=None)

    def test_location_index_validate_min_value(self) -> None:
        with self.assertRaisesMessage(ValidationError, "greater than or equal to 0"):
            TestSeatFactory.create(location_index=-1)

    def test_location_index_unique_per_table(self) -> None:
        seat: Seat = TestSeatFactory.create()

        with self.assertRaisesMessage(ValidationError, "this Table and Location Index already exists"):
            TestSeatFactory.create(
                location_index=seat.location_index,
                table=seat.table
            )

        try:
            TestSeatFactory.create(
                location_index=seat.location_index,
                table=TestTableFactory.create(restaurant=seat.table.restaurant)
            )
        except ValidationError as validate_error:
            self.fail(f"ValidationError raised: {validate_error}")

        try:
            TestSeatFactory.create(
                location_index=TestSeatFactory.create_field_value("location_index"),
                table=seat.table
            )
        except ValidationError as validate_error:
            self.fail(f"ValidationError raised: {validate_error}")

    def test_str(self) -> None:
        seat: Seat = TestSeatFactory.create()

        self.assertIn(str(seat.location_index), str(seat))
        self.assertIn(str(seat.table.number), str(seat))
