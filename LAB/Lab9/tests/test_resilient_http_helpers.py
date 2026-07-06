from email.utils import format_datetime
from datetime import datetime, timedelta, timezone

from library.resilient_http import retry_after_seconds


def test_retry_after_integer_seconds():
    assert retry_after_seconds("7") == 7


def test_retry_after_http_date():
    future = datetime.now(timezone.utc) + timedelta(seconds=5)
    result = retry_after_seconds(format_datetime(future))
    assert 0 <= result <= 5


def test_invalid_retry_after_returns_none():
    assert retry_after_seconds("not-a-delay") is None
