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


def test_set_time_axis_range(qtrace):
    pass


def test_set_axis_datetimes(qtrace):
    pass
