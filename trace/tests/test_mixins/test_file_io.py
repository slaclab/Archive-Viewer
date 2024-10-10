import datetime
from json import dumps
from unittest import mock

import pytest

from config import logger
from mixins.file_io import IOTimeParser
from trace_file_convert import TraceFileConverter

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


@mock.patch("qtpy.QtWidgets.QFileDialog.getSaveFileName")
def test_export_save_file_success(mock_get_save_name, qtrace, tmpdir):
    """Test TraceDisplay.export_save_file() successfully writes a file and it
    matches the expected output.

    Parameters
    ----------
    mock_get_save_name : mock.patch
        Mock qtpy.QtWidgets.QFileDialog.getSaveFileName to return an expected file name
    qtrace : fixture
        Instance of TraceDisplay for application testing
    tmpdir : fixture
         A fixture which will provide a temporary directory unique to each test function

    Expectations
    ------------
    TraceDisplay and TraceFileConverter will make a file with the expected name and content.
    """
    # Construct testcase
    file = tmpdir / "test_export_save_file_success.trc"
    mock_get_save_name.return_value = (file.strpath, None)

    # Construct plot_data to compare against
    plot_data = TraceFileConverter.get_plot_data(qtrace.ui.main_plot)
    for obj in plot_data["y-axes"] + plot_data["curves"] + plot_data["formula"]:
        for k, v in obj.copy().items():
            if v is None:
                del obj[k]

    qtrace.export_save_file()
    assert file.isfile()
    assert file.read() == dumps(plot_data, indent=4)


@mock.patch("qtpy.QtWidgets.QFileDialog.getSaveFileName")
@mock.patch.object(logger, "warning")
def test_export_save_file_dir(mock_warning, mock_get_save_name, qtrace, tmpdir):
    """Test TraceDisplay.export_save_file() is interrupted when the provided filename
    is a directory.

    Parameters
    ----------
    mock_warning : mock.patch
        Mock the logger's warning function to confirm it is only called once
    mock_get_save_name : mock.patch
        Mock qtpy.QtWidgets.QFileDialog.getSaveFileName to return an expected file name
    qtrace : fixture
        Instance of TraceDisplay for application testing
    tmpdir : fixture
         A fixture which will provide a temporary directory unique to each test function

    Expectations
    ------------
    No files/directories should be made and the logger should give a warning.
    """
    # Construct testcase
    mock_get_save_name.return_value = (tmpdir.strpath, None)

    qtrace.export_save_file()
    mock_warning.assert_called_once_with("No file name provided to export save file to")
    assert not tmpdir.isfile()


@mock.patch("qtpy.QtWidgets.QFileDialog.getSaveFileName")
@mock.patch.object(logger, "error")
def test_export_save_file_invalid_extension(mock_error, mock_get_save_name, qtrace, tmpdir):
    """Test TraceDisplay.export_save_file() is interrupted when the provided filename
    has an extension other than *.trc . Needed to make a *.trc file after to prevent
    a recursive loop.

    Parameters
    ----------
    mock_error : mock.patch
        Mock the logger's error function to confirm it is only called once
    mock_get_save_name : mock.patch
        Mock qtpy.QtWidgets.QFileDialog.getSaveFileName to return an expected file name
    qtrace : fixture
        Instance of TraceDisplay for application testing
    tmpdir : fixture
         A fixture which will provide a temporary directory unique to each test function

    Expectations
    ------------
    An error should be given when trying to make the *.csv file, but *.trc succeeds.
    """
    # Construct testcases
    file_csv = tmpdir / "test_export_save_file_invalid_extension.csv"
    file_trc = tmpdir / "test_export_save_file_invalid_extension.trc"
    mock_get_save_name.side_effect = [(file_csv.strpath, None), (file_trc.strpath, None)]

    qtrace.export_save_file()
    mock_error.assert_called_once_with("Incorrect output file format: .csv")
    assert not file_csv.isfile()
    assert file_trc.isfile()


@pytest.mark.parametrize(("test_file_ext"), [".trc", ".xml", ".stp"])
@mock.patch("qtpy.QtWidgets.QFileDialog.getOpenFileName")
def test_import_save_file_success(mock_get_open_name, patch_datetime_now, qtrace, test_file_ext):
    """Test TraceDisplay.import_save_file() successfully opens a save file and
    attempts to setup the application correctly.

    Parameters
    ----------
    mock_get_open_name : mock.patch
        Mock qtpy.QtWidgets.QFileDialog.getOpenFileName to return an expected file name
    qtrace : fixture
        Instance of TraceDisplay for application testing

    Expectations
    ------------
    TraceDisplay and TraceFileConverter will make a file with the expected name and content.
    """
    test_filename = __file__.rsplit("/", 2)[0] + "/test_data/test_file" + test_file_ext
    mock_get_open_name.return_value = (test_filename, None)

    qtrace.import_save_file()
    assert qtrace.curves_model.rowCount() == 2
    # WILL FAIL:
    # axis_table_model.set_model_axes is adding 2 extra for some reason
    # Make test agnostic of other functions
    assert qtrace.axis_table_model.rowCount() == 2


def test_import_save_file_directory(qtrace):
    """Test TraceDisplay.import_save_file() is interrupted when the provided filename
    is either a directory or a nonexistent file.

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing

    Expectations
    ------------
    The logger gives an error and quits early.
    """
    pass


def test_import_save_file_invalid(qtrace):
    """Test TraceDisplay.import_save_file() is interrupted when the provided file
    contains no curves if it's a *.trc file or pvs if it's a *.xml file.

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing

    Expectations
    ------------
    The logger gives an error and prompts the user to select another file.
    """
    pass


def test_import_save_file_hostname(qtrace):
    """Test TraceDisplay.import_save_file() is interrupted when the provided filename
    has a different Archiver URL than expected.

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing

    Expectations
    ------------
    A QMessageBox should be shown for the user to decide whether or not to continue.
    """
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
        exception is expected

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
