from typing import (Union, Optional, Tuple)
from qtpy.QtGui import QColor, QPainter
from qtpy.QtCore import (Qt, QObject, QEvent, QPoint, Slot, Signal,
                         QAbstractTableModel, QModelIndex)
from qtpy.QtWidgets import (QStyledItemDelegate, QSlider, QComboBox, QStyle,
                            QPushButton, QTableView, QStyleOptionViewItem, QWidget)
from pydm.widgets.baseplot_curve_editor import PlotStyleColumnDelegate
from config import logger
from widgets import (ColorButton, CenterCheckbox)
from table_models import ArchiverAxisModel


class SliderDelegate(QStyledItemDelegate):
    """SliderDelegate is a QStyledItemDelegate to display a persistent
    QSlider widget on a QTableView.

    Parameters
    ----------
    parent : QObject
        The parent object for the SliderDelegate.
    table_model : QAbstractTableModel
        The table model to be associated with the SliderDelegate.
    table_view : QTableView
        The table view to be associated with the SliderDelegate.
    init_range : Tuple[int, int], optional
        The range for the QSlider widget, by default (1, 10)
    """
    def __init__(self, parent: Optional[QObject], table_model: QAbstractTableModel,
                 table_view: QTableView, init_range: Tuple[int, int] = (1, 10)):
        super().__init__(parent)
        self.table_model = table_model
        self.table_view = table_view
        self.range = init_range

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """Create a new persistent editor on the Table View at the given index."""
        if option.state == QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        self.table_view.openPersistentEditor(index)

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QSlider:
        """Initialize a QSlider object for use in the Table View."""
        value = self.table_model.data(index, Qt.DisplayRole)
        editor = QSlider(parent, orientation=Qt.Horizontal)
        editor.setFocusPolicy(Qt.StrongFocus)
        editor.setTracking(False)
        editor.setRange(*self.range)
        editor.setValue(value)
        editor.valueChanged.connect(lambda: self.commitData.emit(editor))

        return editor

    def setEditorData(self, editor: QSlider, index: QModelIndex) -> None:
        """Set the editor's data to match the table model's data."""
        value = self.table_model.data(index, Qt.DisplayRole)
        editor.setValue(value)

    def setModelData(self, editor: QSlider, model: QAbstractTableModel, index: QModelIndex) -> None:
        """Set the table model's data to match the editor's data."""
        data = editor.value()
        model.setData(index, data, Qt.EditRole)


class ComboBoxDelegate(QStyledItemDelegate):
    """ComboBoxDelegate is a QStyledItemDelegate to display a persistent
    QComboBox widget on a QTableView.

    Parameters
    ----------
    parent : QObject
        The parent object for the ComboBoxDelegate.
    table_model : QAbstractTableModel
        The table model to be associated with the ComboBoxDelegate.
    table_view : QTableView
        The table view to be associated with the ComboBoxDelegate.
    input : ArchiverAxisModel, list
        The initial dataset to use when populating the QComboBox.
    """
    text_change_signal = Signal(int, str)

    def __init__(self, parent: QObject, table_model: QAbstractTableModel,
                 table_view: QTableView, input: Union[ArchiverAxisModel, list]):
        super().__init__(parent)
        self.table_model = table_model
        self.table_view = table_view
        self.input = input

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """Open a persistent QComboBox on the Table View at the index."""
        self.table_view.openPersistentEditor(index)

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QComboBox:
        """Initialize a QComboBox for use in the Table View."""
        editor = QComboBox(parent)

        logger.debug(f"Setting input to {self.input}")
        if type(self.input) == list:
            editor.addItems(self.input)
        elif type(self.input) == ArchiverAxisModel:
            editor.setModel(self.input)
            editor.setModelColumn(0)

        editor.setFocusPolicy(Qt.StrongFocus)
        editor.setContextMenuPolicy(Qt.CustomContextMenu)
        editor.customContextMenuRequested.connect(self.combo_menu_requested)
        editor.currentIndexChanged.connect(lambda: self.commitData.emit(editor))

        return editor

    def setEditorData(self, editor: QComboBox, index: QModelIndex) -> None:
        """Set the editor's data to match the table model's data."""
        value = self.table_model.data(index, Qt.DisplayRole)
        editor.setCurrentText(value)

    def setModelData(self, editor: QComboBox, model: QAbstractTableModel, index: QModelIndex) -> None:
        """Set the table model's data to match the editor's data."""
        data = editor.currentIndex()
        new_axis_name = editor.currentText()
        self.text_change_signal.emit(index.row(), new_axis_name)
        model.setData(index, data, Qt.EditRole)

    def eventFilter(self, object: QObject, event: QEvent):
        """Disable scrolling for widgets that are not the focus."""
        if event.type() == QEvent.Wheel and not object.hasFocus():
            return True
        return super().eventFilter(object, event)

    @Slot(list)
    def reset_items(self, items: list):
        """"Clear the QComboBox's items and set them to the new list."""
        self.editor.clear()
        self.editor.addItems(items)

    @Slot(QPoint)
    def combo_menu_requested(self, pos: QPoint):
        """Redirect menu requests to the Table View."""
        pos = self.sender().mapToParent(pos)
        self.table_view.customContextMenuRequested.emit(pos)


class CheckboxDelegate(QStyledItemDelegate):
    """CheckboxDelegate is a QStyledItemDelegate to display a persistent
    QCheckbox widget on a QTableView.

    Parameters
    ----------
    parent : QObject
        The parent object for the CheckboxDelegate.
    table_model : QAbstractTableModel
        The table model to be associated with the CheckboxDelegate.
    table_view : QTableView
        The table view to be associated with the CheckboxDelegate.
    """
    def __init__(self, parent: QObject, table_model: QAbstractTableModel, table_view: QTableView):
        super().__init__(parent)
        self.table_model = table_model
        self.table_view = table_view

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """Create a new persistent editor on the Table View at the given index."""
        if option.state == QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        self.table_view.openPersistentEditor(index)

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> CenterCheckbox:
        """Initialize a QCheckbox for use in the Table View."""
        value = self.table_model.data(index, Qt.DisplayRole)
        editor = CenterCheckbox(parent, bool(value))
        editor.toggled.connect(lambda: self.commitData.emit(editor))

        return editor

    def setEditorData(self, editor: CenterCheckbox, index: QModelIndex) -> None:
        """Set the editor's data to match the table model's data."""
        value = self.table_model.data(index, Qt.DisplayRole)
        editor.checkState = bool(value)

    def setModelData(self, editor: CenterCheckbox, model: QAbstractTableModel, index: QModelIndex) -> None:
        """Set the table model's data to match the editor's data."""
        data = editor.checkState
        model.setData(index, data, Qt.EditRole)


class ColorButtonDelegate(QStyledItemDelegate):
    """ColorButtonDelegate is a QStyledItemDelegate to display a persistent
    QPushButton widget on a QTableView that allow's the user to change an object's color.

    Parameters
    ----------
    parent : QObject
        The parent object for the ColorButtonDelegate.
    table_model : QAbstractTableModel
        The table model to be associated with the ColorButtonDelegate.
    table_view : QTableView
        The table view to be associated with the ColorButtonDelegate.
    """
    def __init__(self, parent: QObject, table_model: QAbstractTableModel, table_view: QTableView):
        super().__init__(parent)
        self.table_model = table_model
        self.table_view = table_view

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """Create a new persistent editor on the Table View at the given index."""
        self.table_view.openPersistentEditor(index)

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> ColorButton:
        """Initialize a ColorButton for use in the Table View."""
        value = self.table_model.data(index, Qt.DisplayRole)
        editor = ColorButton(parent, color=value)
        editor.color_changed.connect(lambda: self.commitData.emit(editor))
        return editor

    def setEditorData(self, editor: ColorButton, index: QModelIndex) -> None:
        """Set the editor's data to match the table model's data."""
        value = self.table_model.data(index, Qt.DisplayRole)
        logger.debug("Setting ColorButton data in delegate to: " + value)
        editor.color = QColor(value)

    def setModelData(self, editor: ColorButton, model: QAbstractTableModel, index: QModelIndex) -> None:
        """Set the table model's data to match the editor's data."""
        data = editor.color.name()
        model.setData(index, data, Qt.EditRole)


class CurveStyleDelegate(PlotStyleColumnDelegate):
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """Create a new persistent editor on the Table View at the given index."""
        self.table_view.openPersistentEditor(index)


class DeleteRowDelegate(QStyledItemDelegate):
    """DeleteRowDelegate is a QStyledItemDelegate to display a persistent
    QPushButton widget on a QTableView that allow's the user to delete the row.

    Parameters
    ----------
    parent : QObject
        The parent object for the DeleteRowDelegate.
    table_model : QAbstractTableModel
        The table model to be associated with the DeleteRowDelegate.
    table_view : QTableView
        The table view to be associated with the DeleteRowDelegate.
    """
    def __init__(self, parent: QObject, table_model: QAbstractTableModel, table_view: QTableView):
        super().__init__(parent)
        self.table_model = table_model
        self.table_view = table_view

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """Create a new persistent editor on the Table View at the given index."""
        self.table_view.openPersistentEditor(index)

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> ColorButton:
        """Initialize a QPushButton to delete the table's row."""
        editor = QPushButton(parent)
        icon = editor.style().standardIcon(QStyle.SP_DialogCancelButton)
        editor.setIcon(icon)
        editor.setToolTip("Delete Trace")
        editor.clicked.connect(lambda: self.commitData.emit(editor))
        return editor

    def setModelData(self, editor: ColorButton, model: QAbstractTableModel, index: QModelIndex) -> None:
        """When the setModelData slot is triggered, the row is removed."""
        self.table_model.removeAtIndex(index)
