from typing import (Dict, Any)
from qtpy.QtCore import (Slot, QPoint, QModelIndex, QObject)
from qtpy.QtWidgets import (QHeaderView, QMenu, QAction, QTableView, QDialog,
                            QVBoxLayout, QGridLayout, QLineEdit, QPushButton)
from config import logger
from widgets import (ArchiveSearchWidget, ColorButtonDelegate, CheckboxDelegate,
                     ComboBoxDelegate, CurveStyleDelegate, DeleteRowDelegate)
from table_models import ArchiverCurveModel


class TracesTableMixin:
    """Mixins class for the Traces tab of the settings section."""
    def traces_table_init(self):
        """Initialize the Traces table model and section."""
        self.curves_model = ArchiverCurveModel(self, self.ui.archiver_plot, self.axis_table_model)
        self.curves_model.append()

        self.ui.traces_tbl.setModel(self.curves_model)

        self.menu = PVContextMenu(self)
        self.ui.traces_tbl.customContextMenuRequested.connect(
            self.custom_context_menu)

    def curve_delegates_init(self):
        """Set column delegates for the Traces table to display widgets."""
        # For the Archive Data column, create a Checkbox widget delegate.
        archive_del = CheckboxDelegate(self,
                                       self.curves_model,
                                       self.ui.traces_tbl)
        archive_col = self.curves_model.getColumnIndex("Archive Data")
        self.ui.traces_tbl.setItemDelegateForColumn(archive_col, archive_del)

        # For the Y-Axis Name column, create a ComboBox widget delegate.
        axis_combo_del = ComboBoxDelegate(self,
                                          self.curves_model,
                                          self.ui.traces_tbl,
                                          self.axis_table_model)
        axis_col = self.curves_model.getColumnIndex("Y-Axis Name")
        self.ui.traces_tbl.setItemDelegateForColumn(axis_col, axis_combo_del)
        axis_combo_del.text_change_signal.connect(self.axis_change)

        # For the Color column, create a Color Button widget delegate.
        color_button_del = ColorButtonDelegate(self,
                                               self.curves_model,
                                               self.ui.traces_tbl)
        color_col = self.curves_model.getColumnIndex("Color")
        self.ui.traces_tbl.setItemDelegateForColumn(color_col, color_button_del)

        # For the Style column, use the PyDM CurveStyleDelegate.
        style_del = CurveStyleDelegate(self,
                                       self.curves_model,
                                       self.ui.traces_tbl)
        style_del.toggleColumnVisibility()
        style_col = self.curves_model.getColumnIndex("Style")
        self.ui.traces_tbl.setItemDelegateForColumn(style_col, style_del)

        # Use a delegate to display a button to delete the row.
        delete_row_del = DeleteRowDelegate(self,
                                           self.curves_model,
                                           self.ui.traces_tbl)
        delete_col = self.curves_model.getColumnIndex("")
        self.ui.traces_tbl.setItemDelegateForColumn(delete_col, delete_row_del)

        # Resize the column showing the delete row button.
        hdr = self.ui.traces_tbl.horizontalHeader()
        hdr.setSectionResizeMode(delete_col, QHeaderView.ResizeToContents)

    @Slot(QPoint)
    def custom_context_menu(self, pos: QPoint):
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
    def axis_change(self, row: int, axis_name: str):
        """Slot for connecting a curve to a specified axis.

        Parameters
        ----------
        row : int
            The row of the table associated with the curve changed
        axis_name : str
            The name of the new axis the curve should be on
        """
        curve = self.curves_model.curve_at_index(row)
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

    def __init__(self, parent: QObject = None):
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
    def selected_index(self):
        return self._selected_index

    @selected_index.setter
    def selected_index(self, ind: QModelIndex):
        self._selected_index = ind

    @Slot()
    def import_csv(self):
        # TODO: Add action to import csv
        pass


class FormulaDialog(QDialog):
    def __init__(self, parent: QObject):
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

    def evaluate_formula(self, **kwargs: Dict[str, Any]):
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

    def accept_formula(self, **kwargs: Dict[str, Any]):
        # Retrieve the formula and PV name and perform desired actions
        # TODO: Evaluate the formula before accepting, prompt user if invalid(?)
        formula = self.field.text()
        pv_name = self.pv_name_input.text()

        print("Formula:", formula)
        print("PV Name:", pv_name)

        self.accept()
