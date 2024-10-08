import datetime

import pytest

from mixins.file_io import IOTimeParser

FAKE_TIME = datetime.datetime(2024, 6, 30)


@pytest.fixture(scope="class")
def time_parser():
    """Fixture for an instance of the IOTimeParser.

    Yields
    ------
    An instance of IOTimeParser.
    """
    yield IOTimeParser()


@pytest.fixture
def patch_datetime_now(monkeypatch):
    """Patch to override datetime.datetime.now so that it is an expected value
    that can be tested against.

    Parameters
    ----------
    monkeypatch : fixture
        To override datetime.datetime.now
    """

    class mydatetime(datetime.datetime):
        @classmethod
        def now(cls):
            return FAKE_TIME

    monkeypatch.setattr(datetime, "datetime", mydatetime)


def test_export_save_file(qtrace):
    pass


def test_import_save_file(qtrace):
    pass


@pytest.mark.parametrize(
    # fmt: off
    ("given", "expected"),
    [
        (("+1d", "now"), (None,)),                                      # Relative (+) & Now          -> Exception
        (("+1d", "+1h"), (None,)),                                      # Relative (+) & Relative (+) -> Exception
        (("+1d", "-1h"), (None,)),                                      # Relative (+) & Relative (-) -> Exception
        (("+1d", "2024-06-10"), (None,)),                               # Relative (+) & Absolute     -> Exception
        (("-1d", "now"), ((2024, 6, 29), (2024, 6, 30))),               # Relative (-) & Now
        (("-1d", "+1H"), ((2024, 6, 29), (2024, 6, 29, 1))),            # Relative (-) & Relative (+)
        (("-1d", "-1H"), ((2024, 6, 29), (2024, 6, 29, 23))),           # Relative (-) & Relative (-)
        (("-1d", "2024-06-10"), ((2024, 6, 9), (2024, 6, 10))),         # Relative (-) & Absolute
        (("2024-06-10", "now"), ((2024, 6, 10), (2024, 6, 30))),        # Absolute     & Now
        (("2024-06-10", "+1d"), ((2024, 6, 10), (2024, 6, 11))),        # Absolute     & Relative (+)
        (("2024-06-10", "-1d"), ((2024, 6, 10), (2024, 6, 29))),        # Absolute     & Relative (-)
        (("2024-06-10", "2024-06-20"),((2024, 6, 10), (2024, 6, 20)))   # Absolute     & Absolute
    ],
    # fmt: on
)
def test_time_parser(patch_datetime_now, time_parser, given, expected):
    """Test the IOTimeParser correctly parses start and end strings into datetimes.
    The datetimes may be relative to datetime.now or they may be absolute.

    Parameters
    ----------
    patch_datetime_now : fixture
        To override datetime.datetime.now
    time_parser : fixture
        Instance of IOTimeParser for application testing
    given : tuple
        The given start & end strings to test against
    expected : tuple
        The expected start & end datetimes to be returned. If None, then an
        exception is expected.

    Expectations
    ------------
    IOTimeParser should be able to correctly parse start and end strings that
    are absolute or relative to the current time. If the start time is after the
    current time, that is impossible and will raise an exception. IOTimeParser
    should be able to determine what the base of the relative time should be.
    """
    # Test that expected exceptions get raised
    if expected[0] is None:
        with pytest.raises(ValueError) as exc_info:
            start_dt, end_dt = time_parser.parse_times(*given)
        assert exc_info.type is ValueError
    else:
        # If not expecting an exception, then check start and end datetimes
        start_dt, end_dt = time_parser.parse_times(*given)
        assert start_dt == datetime.datetime(*expected[0])
        assert end_dt == datetime.datetime(*expected[1])
