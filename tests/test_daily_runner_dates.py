import unittest
from datetime import date

from src.mock_generator.schedule import missing_business_dates


class MissingBusinessDatesTests(unittest.TestCase):
    def test_first_run_generates_only_through_date(self):
        self.assertEqual(
            missing_business_dates(None, date(2026, 8, 23)),
            [date(2026, 8, 23)],
        )

    def test_closed_pc_days_are_caught_up(self):
        self.assertEqual(
            missing_business_dates(
                date(2026, 8, 20), date(2026, 8, 23)
            ),
            [date(2026, 8, 21), date(2026, 8, 22), date(2026, 8, 23)],
        )

    def test_no_date_is_generated_twice(self):
        self.assertEqual(
            missing_business_dates(
                date(2026, 8, 23), date(2026, 8, 23)
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()
