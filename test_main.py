import unittest
from unittest.mock import MagicMock
from datetime import datetime, timezone
import main


class TestMain(unittest.TestCase):
    def setUp(self):
        self.session = MagicMock()

    def test_parse_api_response(self):
        rates_json = {
            'date': '2022-01-01',
            'timestamp': 1640995200,
            'base': 'USD',
            'rates': {'EUR': 0.85}
        }
        expected_result = (
            datetime.strptime('2022-01-01', '%Y-%m-%d'),
            1640995200,
            datetime.fromtimestamp(1640995200, tz=timezone.utc),
            'USD',
            {'EUR': 0.85}
        )
        self.assertEqual(main.parse_api_response(rates_json), expected_result)

    def test_insert_new_rates(self):
        rate_date = datetime.strptime('2022-01-01', '%Y-%m-%d')
        epoch_seconds = 1640995200
        date_time = datetime.fromtimestamp(epoch_seconds, tz=timezone.utc)
        base_currency_code = 'USD'
        rate_dict = {'EUR': 0.85}
        main.insert_new_rates(self.session, rate_date, epoch_seconds, date_time, base_currency_code, rate_dict)
        self.session.add.assert_called()
        self.session.commit.assert_called()

    def test_cleanup_old_rates(self):
        oldest_rate_retention_date = datetime.strptime('2022-01-01', '%Y-%m-%d').date()
        main.cleanup_old_rates(self.session, oldest_rate_retention_date)
        self.session.execute.assert_called()
        self.session.commit.assert_called()


if __name__ == '__main__':
    unittest.main()
