from typing import (Dict, Any)
from qtpy import sip
from qtpy.QtCore import (Slot, QPoint, QModelIndex, QObject)
from qtpy.QtWidgets import (QHeaderView, QMenu, QAction, QTableView, QDialog,
                            QVBoxLayout, QGridLayout, QLineEdit, QPushButton)
from pydm.widgets.baseplot import BasePlotCurveItem
from pydm.widgets.baseplot_curve_editor import PlotStyleColumnDelegate
from config import logger
from widgets import (ArchiveSearchWidget, ColorButtonDelegate, ComboBoxDelegate,
                     DeleteRowDelegate, FloatDelegate)
from table_models import ArchiverCurveModel


class TracesTableMixin:
    """Mixins class for the Traces tab of the settings section."""
    def traces_table_init(self) -> None:
        """Initialize the Traces table model and section."""
        self.curves_model = ArchiverCurveModel(self, self.ui.archiver_plot, self.axis_table_model)
        self.curves_model.append()

        self.ui.traces_tbl.setModel(self.curves_model)

        self.menu = PVContextMenu(self)
        self.ui.traces_tbl.customContextMenuRequested.connect(
            self.custom_context_menu)

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
            logger.debug(f"Opening context menu at index {index}")
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
    def __init__(self, parent: QObject) -> None:
        super().__init__(parent)
        self.setWindowTitle("Formula Input")

        # Create the layout for the dialog
        layout = QVBoxLayout(self)

        # Create the QLineEdit for formula input
        self.field = QLineEdit(self)
        layout.addWidget(self.field)

        # Define the list of calculator buttons
        buttons = ["7", "8", "9", "+",
                   "4", "5", "6", "-",
                   "1", "2", "3", "*",
                   "0", "(", ")", "/",
                   ".", "PV", "Clear", "="]

        # Create the calculator buttons and connect them to the input field
        grid_layout = QGridLayout()
        for i, button_text in enumerate(buttons):
            button = QPushButton(button_text, self)
            row = i // 4
            col = i % 4
            grid_layout.addWidget(button, row, col)

            # Connect the button clicked signal to the appropriate action
            if button_text == "PV":
                button.clicked.connect(lambda _: self.field.insert("PV"))
            elif button_text == "Clear":
                button.clicked.connect(lambda _: self.field.clear())
            elif button_text == "=":
                button.clicked.connect(self.evaluate_formula)
            else:
                button.clicked.connect(lambda _, text=button_text: self.field.insert(text))

        layout.addLayout(grid_layout)

        # Add an input field for PV name
        self.pv_name_input = QLineEdit(self)
        self.pv_name_input.setPlaceholderText("Enter PV name")
        layout.addWidget(self.pv_name_input)

        # Add an "OK" button to accept the formula and close the dialog
        ok_button = QPushButton("OK", self)
        ok_button.clicked.connect(self.accept_formula)
        layout.addWidget(ok_button)

    def evaluate_formula(self, **kwargs: Dict[str, Any]) -> None:
        # Evaluate the formula expression and update the formula input field
        # TODO: Check if PVs used are in Table Model
        #   if yes, replace with row header; if no, add to TableModel and replace with row header
        formula = self.field.text()
        try:
            result = eval(formula)
            self.field.setText(str(result))
        except (SyntaxError, TypeError):
            self.field.setText("Error")
            logger.error("Invalid formula evaluated.")

    def accept_formula(self, **kwargs: Dict[str, Any]) -> None:
        # Retrieve the formula and PV name and perform desired actions
        # TODO: Evaluate the formula before accepting, prompt user if invalid(?)
        formula = self.field.text()
        pv_name = self.pv_name_input.text()

        print("Formula:", formula)
        print("PV Name:", pv_name)

        self.accept()
