import random
from datetime import datetime, timedelta
from typing import Any, Iterable

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Manager
from django.utils import timezone

from smartserve.models import Booking, Face, MenuItem, Order, Restaurant, Seat, SeatBooking, Table, User
from smartserve.tests import utils
from smartserve.tests.utils import TestBookingFactory, TestCase, TestFaceFactory, TestMenuItemFactory, TestOrderFactory, TestRestaurantFactory, TestSeatBookingFactory, TestSeatFactory, TestTableFactory, TestUserFactory


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
        invalid_names: set[str] = {
            f" {partial_invalid_name}",
            f"{partial_invalid_name} ",
            f" {partial_invalid_name} "
        }

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

        valid_name: str
        for valid_name in {"The Duke's Head", "The Bad-Tempered Jester"}:
            with self.subTest("Valid unicode name provided", valid_name=valid_name):
                try:
                    TestRestaurantFactory.create(name=valid_name)
                except ValidationError as validate_error:
                    self.fail(f"ValidationError raised: {validate_error}")

    def test_name_validate_min_length(self) -> None:
        with self.assertRaisesMessage(ValidationError, "least 2 characters (it has 1"):
            TestRestaurantFactory.create(
                name=TestRestaurantFactory.create_field_value("name")[:1]
            )

    def test_name_validate_correct_length(self) -> None:
        valid_name_length: int
        for valid_name_length in range(2, 101):
            with self.subTest("Valid length name provided", valid_name_length=valid_name_length):
                try:
                    TestRestaurantFactory.create(
                        name=utils.duplicate_string_to_size(
                            TestRestaurantFactory.create_field_value("name"),
                            size=valid_name_length,
                            strip=True
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
                            TestRestaurantFactory.create_field_value("name"),
                            size=invalid_name_length,
                            strip=True
                        )
                    )

    def test_name_validate_required(self) -> None:
        with self.assertRaisesMessage(ValidationError, "field cannot be null"):
            TestRestaurantFactory.create(name=None)

        with self.assertRaisesMessage(ValidationError, "field cannot be blank"):
            TestRestaurantFactory.create(name="")

    def test_employees_unique(self) -> None:
        restaurant: Restaurant = TestRestaurantFactory.create()
        user: User = TestUserFactory.create()

        restaurant.employees.add(user)
        restaurant.employees.add(user)

        self.assertEqual(1, restaurant.employees.count())

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

    def test_seats_is_manager(self) -> None:
        table: Table = TestTableFactory.create()

        self.assertIsInstance(table.seats, Manager)

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

    def test_bookings_is_manager(self) -> None:
        table: Table = TestTableFactory.create()

        self.assertIsInstance(table.bookings, Manager)

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

        booking: Booking = table.create_booking(
            start_end_pair[0],
            start_end_pair[1],
            [TestFaceFactory.create() for _ in range(5)]
        )

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


class BookingModelTests(TestCase):
    def test_start_validate_required(self) -> None:
        start_end_pair: tuple[datetime, datetime] = TestBookingFactory.create_field_value("start_end_pair")

        with self.assertRaisesMessage(ValidationError, "field cannot be null"):
            TestBookingFactory.create(start=None, end=start_end_pair[1])

    def test_start_validate_before_end(self) -> None:
        time_stamp: float = random.uniform(0, 2524607999.999)

        with self.assertRaisesMessage(ValidationError, "Start Date & Time must be before End"):
            TestBookingFactory.create(
                start=datetime.fromtimestamp(
                    time_stamp + 1000,
                    timezone.get_current_timezone()
                ),
                end=datetime.fromtimestamp(
                    time_stamp,
                    timezone.get_current_timezone()
                )
            )

    def test_end_validate_required(self) -> None:
        start_end_pair: tuple[datetime, datetime] = TestBookingFactory.create_field_value("start_end_pair")

        with self.assertRaisesMessage(ValidationError, "field cannot be null"):
            TestBookingFactory.create(start=start_end_pair[0], end=None)

    def test_restaurant_without_tables(self) -> None:
        booking: Booking = TestBookingFactory.create()

        self.assertIsNone(booking.restaurant)

    def test_restaurant_with_tables(self) -> None:
        booking: Booking = TestBookingFactory.create()

        restaurant: Restaurant = TestSeatBookingFactory.create(
            booking=booking
        ).seat.table.restaurant
        TestSeatBookingFactory.create(
            booking=booking,
            seat__table__restaurant=restaurant
        )

        self.assertEqual(restaurant, booking.restaurant)

    def test_tables_is_manager(self) -> None:
        booking: Booking = TestBookingFactory.create()

        self.assertIsInstance(booking.tables, Manager)

    def test_tables_with_pk(self) -> None:
        booking: Booking = TestBookingFactory.create()
        restaurant: Restaurant = TestRestaurantFactory.create()

        table_pks: set[int] = {
            TestSeatBookingFactory.create(
                booking=booking,
                seat__table__restaurant=restaurant
            ).seat.table.pk,
            TestSeatBookingFactory.create(
                booking=booking,
                seat__table__restaurant=restaurant
            ).seat.table.pk,
            TestSeatBookingFactory.create(
                booking=booking,
                seat__table__restaurant=restaurant
            ).seat.table.pk
        }

        TestSeatBookingFactory.create(seat__table__restaurant=restaurant)
        TestSeatBookingFactory.create(seat__table__restaurant=restaurant)

        self.assertQuerysetEqual(
            Table.objects.filter(pk__in=table_pks),
            booking.tables.all(),
            ordered=False
        )

    def test_tables_without_pk(self) -> None:
        with self.assertRaisesMessage(ValueError, "'Booking' instance needs to have a primary key"):
            TestBookingFactory.create(save=False).tables.all()

    def test_str(self) -> None:
        booking: Booking = TestBookingFactory.create()

        self.assertIn(str(booking.id), str(booking))


class SeatBookingModelTests(TestCase):
    def test_seat_validate_required(self) -> None:
        with self.assertRaisesMessage(ValidationError, "field cannot be null"):
            TestSeatBookingFactory.create(seat=None)

    def test_booking_validate_required(self) -> None:
        with self.assertRaisesMessage(ValidationError, "field cannot be null"):
            TestSeatBookingFactory.create(booking=None)

    def test_face_validate_required(self) -> None:
        with self.assertRaisesMessage(ValidationError, "field cannot be null"):
            TestSeatBookingFactory.create(face=None)

    def test_ordered_menu_items_multiple_of_menu_item(self) -> None:
        menu_item: MenuItem = TestMenuItemFactory.create()
        seat_booking: SeatBooking = TestSeatBookingFactory.create()
        menu_item.available_at_restaurants.add(seat_booking.seat.table.restaurant)

        course: int = TestOrderFactory.create(
            seat_booking=seat_booking,
            menu_item=menu_item
        ).course
        TestOrderFactory.create(
            seat_booking=seat_booking,
            menu_item=menu_item,
            course=course
        )
        seat_booking.ordered_menu_items.add(  # type: ignore
            menu_item,
            through_defaults={"course": course}
        )

        self.assertEqual(2, seat_booking.orders.filter(course=course).count())

    def test_seat_unique_per_booking(self) -> None:
        seat_booking: SeatBooking = TestSeatBookingFactory.create()

        with self.assertRaisesMessage(ValidationError, "this Seat and Booking already exists"):
            TestSeatBookingFactory.create(
                seat=seat_booking.seat,
                booking=seat_booking.booking
            )

        try:
            TestSeatBookingFactory.create(
                seat=seat_booking.seat,
                booking=TestBookingFactory.create()
            )
        except ValidationError as validate_error:
            self.fail(f"ValidationError raised: {validate_error}")

        try:
            TestSeatBookingFactory.create(
                seat=TestSeatFactory.create(table__restaurant=seat_booking.seat.table.restaurant),
                booking=seat_booking.booking
            )
        except ValidationError as validate_error:
            self.fail(f"ValidationError raised: {validate_error}")

    def test_face_unique_in_booking(self) -> None:
        seat_booking: SeatBooking = TestSeatBookingFactory.create()

        with self.assertRaisesMessage(ValidationError, "this Booking and Face already exists"):
            TestSeatBookingFactory.create(
                face=seat_booking.face,
                booking=seat_booking.booking,
                seat__table__restaurant=seat_booking.seat.table.restaurant
            )

    def test_validate_table_restaurant_is_booking_restaurant(self) -> None:
        seat_booking: SeatBooking = TestSeatBookingFactory.create()

        with self.assertRaisesMessage(ValidationError, "same restaurant"):
            TestSeatBookingFactory.create(
                booking=seat_booking.booking,
                seat__table=TestTableFactory.create()
            )

    def test_seat_validate_no_bookings_for_table_at_conflicting_time(self) -> None:
        seat_booking: SeatBooking = TestSeatBookingFactory.create()

        with self.assertRaisesMessage(ValidationError, "booking for this seat's table already exists within these start & end"):
            TestSeatBookingFactory.create(
                seat__table=seat_booking.seat.table,
                booking__start=seat_booking.booking.start + timedelta(seconds=15),
                booking__end=seat_booking.booking.end - timedelta(seconds=15)
            )


class MenuItemModelTests(TestCase):
    def test_name_validate_regex(self) -> None:
        partial_invalid_name: str = TestMenuItemFactory.create_field_value("name")
        invalid_names: set[str] = {
            f" {partial_invalid_name}",
            f"{partial_invalid_name} ",
            f" {partial_invalid_name} "
        }

        unicode_id: int
        for unicode_id in utils.UNICODE_IDS:
            if chr(unicode_id).isalpha():
                continue

            invalid_names.add(chr(unicode_id) * 6)

        invalid_name: str
        for invalid_name in invalid_names:
            with self.subTest("Invalid unicode name provided", invalid_name=invalid_name):
                with self.assertRaisesMessage(ValidationError, "Enter a valid value"):
                    TestMenuItemFactory.create(name=invalid_name)

        valid_name: str
        for valid_name in {"Daisy's Pie", "Slow-Cooked Beef"}:
            with self.subTest("Valid unicode name provided", valid_name=valid_name):
                try:
                    TestMenuItemFactory.create(name=valid_name)
                except ValidationError as validate_error:
                    self.fail(f"ValidationError raised: {validate_error}")

    def test_name_validate_min_length(self) -> None:
        with self.assertRaisesMessage(ValidationError, "least 2 characters (it has 1"):
            TestMenuItemFactory.create(
                name=TestMenuItemFactory.create_field_value("name")[:1]
            )

    def test_name_validate_correct_length(self) -> None:
        valid_name_length: int
        for valid_name_length in range(2, 101):
            with self.subTest("Valid length name provided", valid_name_length=valid_name_length):
                try:
                    TestMenuItemFactory.create(
                        name=utils.duplicate_string_to_size(
                            TestMenuItemFactory.create_field_value("name"),
                            size=valid_name_length,
                            strip=True
                        )
                    )
                except ValidationError as validate_error:
                    self.fail(f"ValidationError raised: {validate_error}")

    def test_name_validate_max_length(self) -> None:
        invalid_name_length: int
        for invalid_name_length in range(101, 105):
            with self.subTest("Too long name provided", invalid_name_length=invalid_name_length):
                with self.assertRaisesMessage(ValidationError, f"most 100 characters (it has {invalid_name_length}"):
                    TestMenuItemFactory.create(
                        name=utils.duplicate_string_to_size(
                            TestMenuItemFactory.create_field_value("name"),
                            size=invalid_name_length,
                            strip=True
                        )
                    )

    def test_name_validate_required(self) -> None:
        with self.assertRaisesMessage(ValidationError, "field cannot be null"):
            TestMenuItemFactory.create(name=None)

        with self.assertRaisesMessage(ValidationError, "field cannot be blank"):
            TestMenuItemFactory.create(name="")

    def test_name_validate_unique(self) -> None:
        menu_item_name: str = TestMenuItemFactory.create().name

        with self.assertRaisesMessage(ValidationError, "Name already exists"):
            TestMenuItemFactory.create(name=menu_item_name)

    def test_description_validate_not_null(self) -> None:
        with self.assertRaisesMessage(IntegrityError, "NOT NULL constraint failed"):
            TestMenuItemFactory.create(description=None)

    def test_str(self) -> None:
        menu_item: MenuItem = TestMenuItemFactory.create()

        self.assertEqual(menu_item.name, str(menu_item))


class OrderModelTests(TestCase):
    def test_menu_item_validate_required(self) -> None:
        with self.assertRaisesMessage(ValidationError, "field cannot be null"):
            TestOrderFactory.create(menu_item=None)

    def test_seat_booking_validate_required(self) -> None:
        with self.assertRaisesMessage(ValidationError, "field cannot be null"):
            TestOrderFactory.create(seat_booking=None)

    def test_course_validate_required(self) -> None:
        with self.assertRaisesMessage(ValidationError, "field cannot be null"):
            TestOrderFactory.create(course=None)

    def test_course_validate_one_of_choices(self) -> None:
        invalid_course: int
        for invalid_course in set(range(-15, 0)) | set(range(4, 25)):
            with self.subTest("Invalid course provided", invalid_course=invalid_course):
                with self.assertRaisesMessage(ValidationError, "not a valid choice"):
                    TestOrderFactory.create(course=invalid_course)

    def test_notes_validate_not_null(self) -> None:
        with self.assertRaisesMessage(IntegrityError, "NOT NULL constraint failed"):
            TestOrderFactory.create(notes=None)

    def test_str(self) -> None:
        order: Order = TestOrderFactory.create()

        self.assertIn(str(order.menu_item), str(order))
        self.assertIn(str(order.seat_booking.seat), str(order))

    def test_menu_item_available_at_restaurant_of_booking(self) -> None:
        menu_item: MenuItem = TestMenuItemFactory.create()
        menu_item.available_at_restaurants.add(TestRestaurantFactory.create())

        with self.assertRaisesMessage(ValidationError, "Only menu items at this booking's restaurant"):
            TestOrderFactory.create(
                menu_item=menu_item,
                seat_booking__seat__table__restaurant=TestRestaurantFactory.create()
            )

        try:
            TestOrderFactory.create(
                menu_item=menu_item,
                seat_booking__seat__table__restaurant=menu_item.available_at_restaurants.first()
            )
        except ValidationError as validate_error:
            self.fail(f"ValidationError raised: {validate_error}")


class FaceModelTests(TestCase):
    def test_image_validate_required(self) -> None:
        with self.assertRaisesMessage(ValueError, "no file associated"):
            TestFaceFactory.create(image=None)

    def test_image_hash_created(self) -> None:
        face: Face = TestFaceFactory.create()

        self.assertTrue(hasattr(face, "image_hash"))
        self.assertIsInstance(face.image_hash, str)
        self.assertEqual(len(face.image_hash), 40)
        try:
            int(face.image_hash, 16)
        except ValueError:
            self.fail("face.image_hash is not valid SHA1 hash.")

    def test_image_hash_validate_unique(self) -> None:
        face: Face = TestFaceFactory.create()

        with self.assertRaisesMessage(ValidationError, "Hash already exists"):
            TestFaceFactory.create(image=face.image)

    def test_gender_value_validate_required(self) -> None:
        with self.assertRaisesMessage(ValidationError, "field cannot be null"):
            TestFaceFactory.create(gender_value=None)

    def test_gender_value_validate_not_zero(self) -> None:
        with self.assertRaisesMessage(ValidationError, "0 is not a valid choice"):
            TestFaceFactory.create(gender_value=0)

    def test_skin_colour_value_validate_required(self) -> None:
        with self.assertRaisesMessage(ValidationError, "field cannot be null"):
            TestFaceFactory.create(skin_colour_value=None)

    def test_skin_colour_value_validate_not_zero(self) -> None:
        with self.assertRaisesMessage(ValidationError, "0 is not a valid choice"):
            TestFaceFactory.create(skin_colour_value=0)

    def test_age_category_validate_required(self) -> None:
        with self.assertRaisesMessage(ValidationError, "field cannot be null"):
            TestFaceFactory.create(age_category=None)

    def test_alt_text(self) -> None:
        face: Face = TestFaceFactory.create()

        self.assertIn(face.get_age_category_display().lower(), face.alt_text)
        self.assertIn(str(face.gender_value), face.alt_text)
        self.assertIn(str(face.skin_colour_value), face.alt_text)
        self.assertIn("AI generated photograph of", face.alt_text)
        self.assertIn("person", face.alt_text)

    def test_str(self) -> None:
        face: Face = TestFaceFactory.create()

        self.assertIn(face.image_hash[:12], str(face))
        self.assertIn(str(face.gender_value), str(face))
        self.assertIn(str(face.skin_colour_value), str(face))
        self.assertIn(str(face.age_category), str(face))
