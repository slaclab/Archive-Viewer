from datetime import datetime

from qtpy.QtCore import QDateTime

from widgets.item_delegates import (
    ComboBoxDelegate,
    DeleteRowDelegate,
    ScientificNotationDelegate,
)


def test_axis_table_delegates(qtrace):
    """Ensure that the axis_tbl's Item Delegates are set correctly.

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing

    Expectations
    ------------
    All of the table's Item Delegates are what the user expects.
    """
    axis_model = qtrace.axis_table_model
    table_view = qtrace.ui.time_axis_tbl

    orientation_col = axis_model.getColumnIndex("Y-Axis Orientation")
    min_range_col = axis_model.getColumnIndex("Min Y Range")
    max_range_col = axis_model.getColumnIndex("Max Y Range")
    delete_col = axis_model.getColumnIndex("")

    assert type(table_view.itemDelegateForColumn(orientation_col)) is ComboBoxDelegate
    assert type(table_view.itemDelegateForColumn(min_range_col)) is ScientificNotationDelegate
    assert type(table_view.itemDelegateForColumn(max_range_col)) is ScientificNotationDelegate
    assert type(table_view.itemDelegateForColumn(delete_col)) is DeleteRowDelegate


def test_set_time_axis_range(qtbot, qtrace):
    """Test the QDateTimeEdits for controlling the start and end times on the main plot's
    X-Axis. The widgets are qtrace.ui.main_start_datetime and qtrace.ui.main_end_datetime.
    Also check that signals are not emitted by qtrace.ui.main_plot.plotItem.vb.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    qtrace : fixture
        Instance of TraceDisplay for application testing

    Expectations
    ------------
    Changing the values of the QDateTimeEdits should change the main plot's X-Range. Signals
    should not be emitted by the main plot's viewbox.
    """
    start_qdt = QDateTime(datetime(2024, 5, 30))
    end_qdt = QDateTime(datetime(2024, 6, 1))

    start_dte = qtrace.ui.main_start_datetime
    end_dte = qtrace.ui.main_end_datetime
    plot_vb = qtrace.ui.main_plot.plotItem.vb

    with qtbot.assertNotEmitted(plot_vb.sigXRangeChanged, wait=500):
        start_dte.setDateTime(start_qdt)
        end_dte.setDateTime(end_qdt)

    start_ts, end_ts = qtrace.ui.main_plot.getXAxis().range
    assert start_ts == start_qdt.toSecsSinceEpoch()
    assert end_ts == end_qdt.toSecsSinceEpoch()


def test_set_axis_datetimes_programatically(qtbot, qtrace):
    """Test that changing the X-Axis range (programatically) changes the QDateTimeEdit
    values to match. The widgets are qtrace.ui.main_start_datetime and
    qtrace.ui.main_end_datetime.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    qtrace : fixture
        Instance of TraceDisplay for application testing

    Expectations
    ------------
    Setting the range for the X-Axis will cause the QDateTimeEdits to update thier
    values. Signals should not be emitted by the QDateTimeEdits.
    """
    start_dte = qtrace.ui.main_start_datetime
    end_dte = qtrace.ui.main_end_datetime
    signals = [start_dte.dateTimeChanged, end_dte.dateTimeChanged]

    plot_vb = qtrace.ui.main_plot.plotItem.vb
    start_qdt = QDateTime(2024, 5, 30, 0, 0, 0)
    end_qdt = QDateTime(2024, 6, 1, 0, 0, 0)

    with qtbot.assertNotEmitted(signals[0], wait=500), qtbot.assertNotEmitted(signals[1], wait=500):
        plot_vb.setXRange(start_qdt.toSecsSinceEpoch(), end_qdt.toSecsSinceEpoch(), padding=0)

    assert start_dte.dateTime() == start_qdt
    assert end_dte.dateTime() == end_qdt


def test_set_axis_datetimes_manually(qtbot, qtrace):
    """Test that changing the X-Axis range (manually) changes the QDateTimeEdit
    values to match. The widgets are qtrace.ui.main_start_datetime and
    qtrace.ui.main_end_datetime.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    qtrace : fixture
        Instance of TraceDisplay for application testing

    Expectations
    ------------
    Using the scrollwheel on the X-Axis will cause the QDateTimeEdits to update
    thier values. Signals should not be emitted by the QDateTimeEdits.
    """
    start_dte = qtrace.ui.main_start_datetime
    end_dte = qtrace.ui.main_end_datetime
    signals = [start_dte.dateTimeChanged, end_dte.dateTimeChanged]

    # Set the X-Axis without changing the QDateTimeEdits
    plot_vb = qtrace.ui.main_plot.plotItem.vb
    start_qdt = QDateTime(2024, 5, 30, 0, 0, 0)
    end_qdt = QDateTime(2024, 6, 1, 0, 0, 0)
    qtrace.set_time_axis_range((start_qdt, end_qdt))

    # Mimic scrolling the mouse wheel on the X-Axis, triggers qtrace.set_axis_datetimes()
    with qtbot.assertNotEmitted(signals[0], wait=500), qtbot.assertNotEmitted(signals[1], wait=500):
        plot_vb.sigRangeChangedManually.emit([])

    assert start_dte.dateTime() == start_qdt
    assert end_dte.dateTime() == end_qdt
