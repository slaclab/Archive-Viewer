from typing import Dict, Any
from qtpy.QtGui import QKeyEvent
from qtpy import sip
from qtpy.QtCore import (Slot, QPoint, QModelIndex, QObject, Qt)
from qtpy.QtWidgets import (QHeaderView, QMenu, QAction, QTableView, QDialog,
                            QVBoxLayout, QGridLayout, QLineEdit, QPushButton, QAbstractItemView, QTableWidget)
from pydm.widgets.baseplot import BasePlotCurveItem
from pydm.widgets.baseplot_curve_editor import PlotStyleColumnDelegate
from config import logger
from pydm.widgets.archiver_time_plot import FormulaCurveItem
from widgets import (
    ArchiveSearchWidget,
    ColorButtonDelegate,
    ComboBoxDelegate,
    DeleteRowDelegate,
    FloatDelegate,
    InsertPVDelegate
)
from table_models import ArchiverCurveModel


class TracesTableMixin:
    """Mixins class for the Traces tab of the settings section."""
    def traces_table_init(self) -> None:
        """Initialize the Traces table model and section."""
        self.curves_model = ArchiverCurveModel(self, self.ui.archiver_plot, self.axis_table_model)
        self.curves_model.append()

        self.ui.traces_tbl.setModel(self.curves_model)

        self.menu = PVContextMenu(self)
        self.ui.traces_tbl.customContextMenuRequested.connect(self.custom_context_menu)

        hdr = self.ui.traces_tbl.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.Stretch)
        channel_col = self.curves_model.getColumnIndex("Channel")
        hdr.setSectionResizeMode(channel_col, QHeaderView.ResizeToContents)
        del_col = self.curves_model.getColumnIndex("")
        hdr.setSectionResizeMode(del_col, QHeaderView.ResizeToContents)

    def curve_delegates_init(self) -> None:
        """Set column delegates for the Traces table to display widgets."""
        axis_col = self.curves_model.getColumnIndex("Y-Axis Name")
        axis_combo_del = ComboBoxDelegate(self.ui.traces_tbl, self.axis_table_model)
        axis_combo_del.sigTextChange.connect(self.axis_change)
        self.ui.traces_tbl.setItemDelegateForColumn(axis_col, axis_combo_del)

        color_col = self.curves_model.getColumnIndex("Color")
        color_button_del = ColorButtonDelegate(self.ui.traces_tbl)
        self.ui.traces_tbl.setItemDelegateForColumn(color_col, color_button_del)

        style_col = self.curves_model.getColumnIndex("Style")
        style_del = PlotStyleColumnDelegate(self,
                                       self.curves_model,
                                       self.ui.traces_tbl)
        style_del.toggleColumnVisibility()
        self.ui.traces_tbl.setItemDelegateForColumn(style_col, style_del)

        styles = BasePlotCurveItem.lines
        line_style_col = self.curves_model.getColumnIndex("Line Style")
        line_style_del = ComboBoxDelegate(self.ui.traces_tbl, styles)
        self.ui.traces_tbl.setItemDelegateForColumn(line_style_col, line_style_del)

        size_data = {f"{i}px": i for i in range(1, 6)}
        line_width_col = self.curves_model.getColumnIndex("Line Width")
        line_width_del = ComboBoxDelegate(self.ui.traces_tbl, size_data)
        self.ui.traces_tbl.setItemDelegateForColumn(line_width_col, line_width_del)

        symbols = BasePlotCurveItem.symbols
        symbol_col = self.curves_model.getColumnIndex("Symbol")
        symbol_del = ComboBoxDelegate(self.ui.traces_tbl, symbols)
        self.ui.traces_tbl.setItemDelegateForColumn(symbol_col, symbol_del)

        size_data = {f"{i}px": i for i in range(5, 26, 5)}
        symbol_size_col = self.curves_model.getColumnIndex("Symbol Size")
        symbol_size_del = ComboBoxDelegate(self.ui.traces_tbl, size_data)
        self.ui.traces_tbl.setItemDelegateForColumn(symbol_size_col, symbol_size_del)

        bar_width_col = self.curves_model.getColumnIndex("Bar Width")
        bar_width_del = FloatDelegate(self.ui.traces_tbl, init_range=(.1, 5))
        self.ui.traces_tbl.setItemDelegateForColumn(bar_width_col, bar_width_del)

        upper_limit_col = self.curves_model.getColumnIndex("Upper Limit")
        upper_limit_del = FloatDelegate(self.ui.traces_tbl, init_range=(0, float("inf")))
        self.ui.traces_tbl.setItemDelegateForColumn(upper_limit_col, upper_limit_del)

        lower_limit_col = self.curves_model.getColumnIndex("Lower Limit")
        lower_limit_del = FloatDelegate(self.ui.traces_tbl, init_range=(0, float("inf")))
        self.ui.traces_tbl.setItemDelegateForColumn(lower_limit_col, lower_limit_del)

        limit_color_col = self.curves_model.getColumnIndex("Limit Color")
        limit_color_del = ColorButtonDelegate(self.ui.traces_tbl)
        self.ui.traces_tbl.setItemDelegateForColumn(limit_color_col, limit_color_del)

        delete_col = self.curves_model.getColumnIndex("")
        delete_row_del = DeleteRowDelegate(self.ui.traces_tbl)
        self.ui.traces_tbl.setItemDelegateForColumn(delete_col, delete_row_del)

    @Slot(QPoint)
    def custom_context_menu(self, pos: QPoint) -> None:
        """Open a custom context menu for the Traces table where the
        user right-clicks. If the ColorButton is right-clicked, then do
        not open a context menu.

        Parameters
        ----------
        pos : QPoint
            The position where the context menu should appear
        """
        table = self.ui.traces_tbl
        if not table or not isinstance(table, QTableView):
            logger.error(f"Internal error: {type(table)} is not QTableView")
            return

        index = table.indexAt(pos)
        is_color = index.column() == self.curves_model.getColumnIndex("Color")
        logger.debug(f"ColorButton column selected: {is_color}")

        if index.isValid() and not is_color:
            self.menu.selected_index = index
            self.menu.popup(table.viewport().mapToGlobal(pos))

    @Slot(int, str)
    def axis_change(self, row: int, axis_name: str) -> None:
        """Slot for connecting a curve to a specified axis.

        Parameters
        ----------
        row : int
            The row of the table associated with the curve changed
        axis_name : str
            The name of the new axis the curve should be on
        """
        if not axis_name:
            return
        # Get the curve and check if it has been deleted
        curve = self.curves_model.curve_at_index(row)
        if not sip.isdeleted(curve):
            self.ui.archiver_plot.plotItem.linkDataToAxis(curve, axis_name)


class PVContextMenu(QMenu):
    # TODO: Change this QMenu so functions that change data stay in table object
    #   - Move functions to table widget
    #   - Init parameters: dict("ACTION_NAME": function)
    #   - Init: Loop through dict values:
    #       - Create action w/ name
    #       - action.triggered.connect(function)
    #       - self.addAction(action)

    # data_changed_signal = Signal(int)

    # TODO: Archived PVs are no longer draggable from the search tool. Find out why

    def __init__(self, parent: QObject = None) -> None:
        super().__init__(parent)
        self._selected_index = None
        self.archive_search = ArchiveSearchWidget()
        self._formula_dialog = FormulaDialog(self)

        # Add "SEARCH PV" option
        search_pv_action = QAction("SEARCH PV", self)
        search_pv_action.triggered.connect(self.archive_search.show)
        self.addAction(search_pv_action)

        # Add "FORMULA" option
        formula_action = QAction("FORMULA", self)
        formula_action.triggered.connect(self._formula_dialog.exec_)
        self.addAction(formula_action)

        import_action = QAction("IMPORT CSV", self)
        import_action.triggered.connect(self.import_csv)
        self.addAction(import_action)

    @property
    def selected_index(self) -> QModelIndex:
        """Get the table's selected index."""
        return self._selected_index

    @selected_index.setter
    def selected_index(self, ind: QModelIndex) -> None:
        """Set the table's selected index."""
        self._selected_index = ind

    @Slot()
    def import_csv(self) -> None:
        # TODO: Add action to import csv
        pass


class FormulaDialog(QDialog):
    """Formula Dialog - when a user right clicks on a row in the list of curves, they have the option to input a formula
    They could opt to type it instead, but this opens a box that is a nicer UI for inputting a formula."""
    def __init__(self, parent: QObject) -> None:
        super().__init__(parent)
        self.setWindowTitle("Formula Input")

        # Create the layout for the dialog
        layout = QVBoxLayout(self)
        # Create the QLineEdit for formula input
        self.field = QLineEdit(self)
        self.curveModel = self.parent().parent().curves_model
        self.pv_list = QTableView(self)
        #We're going to copy the list of PVs from the curve model. We're also not going to allow the user to make edits to the list of PVs
        self.pv_list.setModel(self.curveModel)
        self.pv_list.setEditTriggers(QAbstractItemView.EditTriggers(0))
        self.pv_list.setMaximumWidth(1000)
        header = self.pv_list.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, self.curveModel.columnCount() - 1):
            # Hide all columns that arent useful, but keep one left over to add a button to
            self.pv_list.setColumnHidden(i, True)
        insertButton = InsertPVDelegate(self.pv_list, self.curveModel)
        insertButton.button_clicked.connect(self.field.insert)
        self.pv_list.setItemDelegateForColumn(self.curveModel.columnCount() - 1, insertButton)
        layout.addWidget(self.pv_list)
        layout.addWidget(self.field)

        self.index = self.parent().selected_index

        # Define the list of calculator buttons.
        # It's a bunch of preset buttons, but users can type other functions under math.
        buttons = ["7",       "8",     "9",      "+",     "(",      ")",
                   "4",       "5",     "6",      "-",    "^2", "sqrt()",
                   "1",       "2",     "3",      "*",   "^-1",  "ln()",
                   "0",       "e",    "pi",      "/", "sin()", "asin()",
                   ".",   "abs()", "min()",      "^", "cos()", "acos()",
                   "PV",  "Clear", "max()", "mean()", "tan()", "atan()"]

        # Create the calculator buttons and connect them to the input field
        grid_layout = QGridLayout()
        for i, button_text in enumerate(buttons):
            button = QPushButton(button_text, self)
            row = i // 6
            col = i % 6
            grid_layout.addWidget(button, row, col)
            # Connect the button clicked signal to the appropriate action
            # PV currently does nothing, this is a remnant
            # From when we would have the pv_list open in a new window
            if button_text == "PV":
                # TODO: Either give a function for this button or replace it
                pass
            elif button_text == "Clear":
                button.clicked.connect(lambda _: self.field.clear())
            else:
                button.clicked.connect(lambda _, text=button_text: self.field.insert(text))
        layout.addLayout(grid_layout)

        # Add an "OK" button to accept the formula and close the dialog
        ok_button = QPushButton("OK", self)
        ok_button.clicked.connect(self.accept_formula)
        layout.addWidget(ok_button)

    def keyPressEvent(self, e: QKeyEvent) -> None:
        # Special key press tracker, just so that if enter or return is pressed the formula dialog attempts to submit the formula
        if e.key() == Qt.Key_Return or e.key() == Qt.Key_Enter:
            self.accept_formula()
        return super().keyPressEvent(e)

    def exec_(self):
        """ When the formula dialog is opened (every time) we need to
            update it with the latest information on the curve model and
            also populate the text box with the pre-existing formula (if it already was there)"""
        self.index = self.parent().selected_index
        self.pv_list.setRowHidden(len(self.curveModel._row_names) - 1, True)
        for i in range(self.curveModel.rowCount() - 1):
            self.pv_list.setRowHidden(i, False)
        index = self.curveModel.index(self.index.row(), 0)
        curve = self.curveModel._plot._curves[self.index.row()]
        if index.data() and isinstance(curve, FormulaCurveItem):
            self.field.setText(str(index.data()).strip("f://"))
        else:
            self.field.setText("")
        super().exec_()

    def accept_formula(self, **kwargs: Dict[str, Any]) -> None:
        # Retrieve the formula and PV name and perform desired actions
        # We take in the formula (prepend the formula tag) and attempt to create a curve. Iff it passes, we close the window
        formula = "f://" + self.field.text()
        # pv_name = self.pv_name_input.text()
        passed = self.curveModel.replaceToFormula(index = self.curveModel.index(self.parent().selected_index.row(), 0), formula = formula)
        if passed:
            self.field.setText("")
            self.accept()
