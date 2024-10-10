from widgets.item_delegates import (
    ComboBoxDelegate,
    DeleteRowDelegate,
    ColorButtonDelegate,
)


def test_traces_table_delegates(qtrace):
    """Ensure that the traces_tbl's Item Delegates are set correctly.

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing

    Expectations
    ------------
    All of the table's Item Delegates are what the user expects.
    """
    curves_model = qtrace.curves_model
    table_view = qtrace.ui.traces_tbl

    axis_col = curves_model.getColumnIndex("Y-Axis Name")
    color_col = curves_model.getColumnIndex("Color")
    style_col = curves_model.getColumnIndex("Style")
    line_style_col = curves_model.getColumnIndex("Line Style")
    line_width_col = curves_model.getColumnIndex("Line Width")
    symbol_col = curves_model.getColumnIndex("Symbol")
    symbol_size_col = curves_model.getColumnIndex("Symbol Size")
    delete_col = curves_model.getColumnIndex("")

    assert type(table_view.itemDelegateForColumn(axis_col)) is ComboBoxDelegate
    assert type(table_view.itemDelegateForColumn(color_col)) is ColorButtonDelegate
    assert type(table_view.itemDelegateForColumn(style_col)) is ComboBoxDelegate
    assert type(table_view.itemDelegateForColumn(line_style_col)) is ComboBoxDelegate
    assert type(table_view.itemDelegateForColumn(line_width_col)) is ComboBoxDelegate
    assert type(table_view.itemDelegateForColumn(symbol_col)) is ComboBoxDelegate
    assert type(table_view.itemDelegateForColumn(symbol_size_col)) is ComboBoxDelegate
    assert type(table_view.itemDelegateForColumn(delete_col)) is DeleteRowDelegate


def test_drag_drop(qtrace):
    pass


def test_context_menu(qtrace):
    pass


def test_formula_dialog(qtrace):
    pass
