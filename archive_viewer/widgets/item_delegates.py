from typing import (Union, Tuple)
from qtpy.QtGui import (QColor, QPainter, QRegExpValidator)
from qtpy.QtCore import (Qt, QObject, QEvent, QPoint, Slot, Signal, QRegExp,
                         QAbstractTableModel, QModelIndex, QAbstractItemModel)
from qtpy.QtWidgets import (QStyledItemDelegate, QSlider, QComboBox, QStyle,
                            QPushButton, QTableView, QStyleOptionViewItem,
                            QWidget, QDoubleSpinBox, QLineEdit)
from config import logger
from widgets import (ColorButton, CenterCheckbox)


class SliderDelegate(QStyledItemDelegate):
    """SliderDelegate is a QStyledItemDelegate to display a persistent
    QSlider widget on a QTableView.

    Parameters
    ----------
    parent : QTableView
        The parent object for the SliderDelegate. Should be the
        associated QTableView
    init_range : Tuple[int, int], optional
        The range for the QSlider widget, by default (1, 10)
    """
    def __init__(self, parent: QTableView, init_range: Tuple[int, int] = (1, 10)) -> None:
        super().__init__(parent)
        self.init_range = init_range
        self.editor_list = []

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """Create a new persistent editor on the Table View at the given index."""
        if index.row() >= len(self.editor_list):
            self.parent().openPersistentEditor(index)
        return super().paint(painter, option, index)

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QSlider:
        """Initialize a QSlider object for use in the Table View."""
        if index.row() >= len(self.editor_list):
            value = index.data(Qt.DisplayRole)
            editor = QSlider(orientation=Qt.Horizontal, parent=parent)
            editor.setFocusPolicy(Qt.StrongFocus)
            editor.setRange(*self.init_range)
            editor.setTickPosition(QSlider.TicksBothSides)
            editor.setTickInterval(1)
            editor.setValue(value)
            editor.valueChanged.connect(lambda: self.commitData.emit(editor))

            self.editor_list.append(editor)
            return editor
        return super().createEditor(parent, option, index)

    def destroyEditor(self, editor: QSlider, index: QModelIndex) -> None:
        """Close the persistent editor for a defined index."""
        if index.row() < len(self.editor_list):
            del self.editor_list[index.row()]
            editor.deleteLater()
            self.parent().closePersistentEditor(index)
            return
        return super().destroyEditor(editor, index)

    def setEditorData(self, editor: QSlider, index: QModelIndex) -> None:
        """Set the editor's data to match the table model's data."""
        value = index.data(Qt.DisplayRole)
        editor.setValue(value)

    def setModelData(self, editor: QSlider, model: QAbstractTableModel, index: QModelIndex) -> None:
        """Set the table model's data to match the editor's data."""
        data = editor.value()
        model.setData(index, data, Qt.EditRole)

    def eventFilter(self, object: QObject, event: QEvent):
        """Disable scrolling for widgets that are not the focus."""
        if event.type() == QEvent.Wheel and not object.hasFocus():
            return True
        return super().eventFilter(object, event)


class ComboBoxDelegate(QStyledItemDelegate):
    """ComboBoxDelegate is a QStyledItemDelegate to display a persistent
    QComboBox widget on a QTableView.

    Parameters
    ----------
    parent : QTableView
        The parent object for the ComboBoxDelegate. Should be the
        associated QTableView
    data_source : ArchiverAxisModel, list, dict
        The initial dataset to use when populating the QComboBox.
    """
    sigTextChange = Signal(int, str)

    def __init__(self, parent: QTableView, data_source: Union[QAbstractItemModel, list, dict]) -> None:
        super().__init__(parent)
        if isinstance(data_source, list):
            data_source = {v: v for v in data_source}
        self.data_source = data_source
        self.editor_list = []

    def initStyleOption(self, option: QStyleOptionViewItem, index: QModelIndex):
        """Initialize a QComboBox for use in the Table View."""
        if index.row() >= len(self.editor_list):
            editor = QComboBox()

            logger.debug(f"Setting input to {self.data_source}")
            if isinstance(self.data_source, dict):
                editor.addItems(self.data_source.keys())
                value = index.data(Qt.DisplayRole)
                if str(value) in self.data_source:
                    editor.setCurrentText(str(value))
                else:
                    value_ind = list(self.data_source.values()).index(value)
                    editor.setCurrentIndex(value_ind)
            elif isinstance(self.data_source, QAbstractItemModel):
                editor.setModel(self.data_source)
                editor.setModelColumn(0)
                editor.setCurrentIndex(editor.count() - 1)
            editor.setFocusPolicy(Qt.StrongFocus)
            editor.setContextMenuPolicy(Qt.CustomContextMenu)
            editor.customContextMenuRequested.connect(self.combo_menu_requested)
            editor.currentIndexChanged.connect(lambda: self.commitData.emit(editor))

            self.editor_list.append(editor)
            self.parent().setIndexWidget(index, editor)
        return super().initStyleOption(option, index)

    def destroyEditor(self, editor: QComboBox, index: QModelIndex) -> None:
        """Destroy the editor for a defined index."""
        if index.row() < len(self.editor_list):
            logger.debug(f"Removing {self.editor_list[index.row()]} from delegate")
            self.editor_list[index.row()].deleteLater()
            del self.editor_list[index.row()]
            return
        return super().destroyEditor(editor, index)

    def setModelData(self, editor: QComboBox, model: QAbstractTableModel, index: QModelIndex) -> None:
        """Set the table model's data to match the editor's data."""
        curr_text = editor.currentText()
        if isinstance(self.data_source, dict):
            data = self.data_source[curr_text]
        elif isinstance(self.data_source, QAbstractItemModel):
            self.sigTextChange.emit(index.row(), curr_text)
            data = curr_text
        model.setData(index, data, Qt.EditRole)

    def setEditorData(self, editor: QComboBox, index: QModelIndex) -> None:
        """Set the editor's data to match the table model's data."""
        value = index.data(Qt.DisplayRole)
        editor.setCurrentText(value)

    def eventFilter(self, object: QObject, event: QEvent) -> bool:
        """Disable scrolling for widgets that are not the focus."""
        if event.type() == QEvent.Wheel and not object.hasFocus():
            return True
        return super().eventFilter(object, event)

    @Slot(QPoint)
    def combo_menu_requested(self, pos: QPoint) -> None:
        """Redirect menu requests to the Table View."""
        pos = self.sender().mapToParent(pos)
        self.parent().customContextMenuRequested.emit(pos)


class CheckboxDelegate(QStyledItemDelegate):
    """CheckboxDelegate is a QStyledItemDelegate to display a persistent
    QCheckbox widget on a QTableView.

    Parameters
    ----------
    parent : QTableView
        The parent object for the CheckboxDelegate. Should be the
        associated QTableView
    """
    def __init__(self, parent: QTableView) -> None:
        super().__init__(parent)
        self.editor_list = []

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """Create a new persistent editor on the Table View at the given index."""
        if index.row() >= len(self.editor_list):
            self.parent().openPersistentEditor(index)
        return super().paint(painter, option, index)

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> CenterCheckbox:
        """Initialize a QCheckbox for use in the Table View."""
        if index.row() >= len(self.editor_list):
            value = index.data(Qt.DisplayRole)
            editor = CenterCheckbox(parent, bool(value))
            editor.toggled.connect(lambda: self.commitData.emit(editor))

            self.editor_list.append(editor)
            return editor
        return super().createEditor(parent, option, index)

    def destroyEditor(self, editor: CenterCheckbox, index: QModelIndex) -> None:
        """Close the persistent editor for a defined index."""
        if index.row() < len(self.editor_list):
            del self.editor_list[index.row()]
            editor.deleteLater()
            self.parent().closePersistentEditor(index)
            return
        return super().destroyEditor(editor, index)

    def setEditorData(self, editor: CenterCheckbox, index: QModelIndex) -> None:
        """Set the editor's data to match the table model's data."""
        value = index.data(Qt.DisplayRole)
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
    parent : QTableView
        The parent object for the ColorButtonDelegate. Should be the
        associated QTableView
    """
    def __init__(self, parent: QTableView) -> None:
        super().__init__(parent)
        self.editor_list = []

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """Create a new persistent editor on the Table View at the given index."""
        if index.row() >= len(self.editor_list):
            self.parent().openPersistentEditor(index)
        return super().paint(painter, option, index)

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> ColorButton:
        """Initialize a ColorButton for use in the Table View."""
        if index.row() >= len(self.editor_list):
            value = index.data(Qt.DisplayRole)
            editor = ColorButton(parent, color=value)
            editor.color_changed.connect(lambda: self.commitData.emit(editor))

            self.editor_list.append(editor)
            return editor
        return super().createEditor(parent, option, index)

    def destroyEditor(self, editor: ColorButton, index: QModelIndex) -> None:
        """Close the persistent editor for a defined index."""
        if index.row() < len(self.editor_list):
            del self.editor_list[index.row()]
            editor.deleteLater()
            self.parent().closePersistentEditor(index)
            return
        return super().destroyEditor(editor, index)

    def setEditorData(self, editor: ColorButton, index: QModelIndex) -> None:
        """Set the editor's data to match the table model's data."""
        value = index.data(Qt.DisplayRole)
        logger.debug("Setting ColorButton data in delegate to: " + value)
        editor.color = QColor(value)

    def setModelData(self, editor: ColorButton, model: QAbstractTableModel, index: QModelIndex) -> None:
        """Set the table model's data to match the editor's data."""
        data = editor.color.name()
        model.setData(index, data, Qt.EditRole)


class DeleteRowDelegate(QStyledItemDelegate):
    """DeleteRowDelegate is a QStyledItemDelegate to display a persistent
    QPushButton widget on a QTableView that allow's the user to delete the row.

    Parameters
    ----------
    parent : QTableView
        The parent object for the DeleteRowDelegate. Should be the
        associated QTableView
    """
    def __init__(self, parent: QTableView) -> None:
        super().__init__(parent)
        self.editor_list = []

    def initStyleOption(self, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """Initialize a QPushButton to delete the table's row."""
        logger.debug("called method: DeleteRowDelegate.initStyleOption")
        if index.row() >= len(self.editor_list):
            editor = QPushButton(self.parent())
            icon = editor.style().standardIcon(QStyle.SP_DialogCancelButton)
            editor.setIcon(icon)
            editor.setToolTip("Delete Row")
            editor.clicked.connect(lambda: self.commitData.emit(editor))

            self.editor_list.append(editor)
            self.parent().setIndexWidget(index, editor)

        return super().initStyleOption(option, index)

    def destroyEditor(self, editor: QWidget, index: QModelIndex) -> None:
        """Destroy the editor for a defined index."""
        if index.row() < len(self.editor_list):
            logger.debug(f"Removing {self.editor_list[index.row()]} from delegate")
            self.editor_list[index.row()].deleteLater()
            del self.editor_list[index.row()]
            return
        return super().destroyEditor(editor, index)

    def setModelData(self, _: QPushButton, model: QAbstractTableModel, index: QModelIndex) -> None:
        """When the setModelData slot is triggered, the row is removed."""
        model.removeAtIndex(index)
class InsertPVDelegate(QStyledItemDelegate):
    """InsertPVDelegate is a QStyledItemDelegate to display a persistent
    QPushButton widget on the FormulaDialog that allow's the user to insert the PV.

    Parameters
    ----------
    parent : FormulaDialog
        The parent object for the InsertPVDelegate. Should be the
        associated QTableView
    """
    button_clicked = Signal(str)
    def __init__(self, parent: QTableView, model: QAbstractItemModel) -> None:
        super().__init__(parent)
        self.editor_list = []
        self.model = model

    def initStyleOption(self, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """Initialize a QPushButton to insert the table's header."""
        logger.debug("called method: InsertPVDelegate.initStyleOption")
        if index.row() >= len(self.editor_list):
            editor = QPushButton(self.parent())
            editor.setText("Insert")
            editor.setToolTip("Insert PV")
            #We don't want to allow people to select the button, only click it
            editor.setFocusPolicy(Qt.NoFocus)
            editor.pressed.connect(lambda: self.button_clicked.emit("{"+ self.model._row_names[index.row()]+"}"))
            self.editor_list.append(editor)
            self.parent().setIndexWidget(index, editor)

        return super().initStyleOption(option, index)

    def destroyEditor(self, editor: QWidget, index: QModelIndex) -> None:
        """Destroy the editor for a defined index."""
        if index.row() < len(self.editor_list):
            logger.debug(f"Removing {self.editor_list[index.row()]} from delegate")
            self.editor_list[index.row()].deleteLater()
            del self.editor_list[index.row()]
            return
        return super().destroyEditor(editor, index)

class FloatDelegate(QStyledItemDelegate):
    """FloatDelegate is a QStyledItemDelegate to display a
    QDoubleSpinbox on a table.

    Parameters
    ----------
    parent : QTableView
        The delegate's associated QTableView.
    init_range : Tuple[float, float], optional
        The min/max range for the QDoubleSpinBox, by default
        (float("-inf"), float("inf"))
    prec : int, optional
        The float's precision, by default 2
    """
    def __init__(self, parent: QTableView, init_range: Tuple[float, float] = (float("-inf"), float("inf")), prec: int = 2) -> None:
        super().__init__(parent)
        self.range = init_range
        self.prec = prec
        self.editor_list = []

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """Create a new persistent editor on the Table View at the given index."""
        if index.row() >= len(self.editor_list):
            self.parent().openPersistentEditor(index)
            editor = self.editor_list[-1]
            editor.lineEdit().deselect()
        return super().paint(painter, option, index)

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QDoubleSpinBox:
        """Initialize a QDoubleSpinBox to delete the table's row."""
        if index.row() >= len(self.editor_list):
            value = index.data(Qt.DisplayRole)
            if value is None:
                value = self.range[0]

            editor = QDoubleSpinBox(parent)
            editor.setMinimum(self.range[0])
            editor.setMaximum(self.range[1])
            editor.setDecimals(self.prec)
            editor.setValue(value)
            editor.editingFinished.connect(lambda: self.commitData.emit(editor))

            self.editor_list.append(editor)
            return editor
        return super().createEditor(parent, option, index)

    def destroyEditor(self, editor: QDoubleSpinBox, index: QModelIndex) -> None:
        """Close the persistent editor for a defined index."""
        if index.row() < len(self.editor_list):
            del self.editor_list[index.row()]
            editor.deleteLater()
            self.parent().closePersistentEditor(index)
            return
        return super().destroyEditor(editor, index)

    def setEditorData(self, editor: QDoubleSpinBox, index: QModelIndex) -> None:
        """Set the editor's data to match the table model's data."""
        value = index.data(Qt.DisplayRole)
        editor.setValue(value)
        editor.lineEdit().deselect()

    def setModelData(self, editor: QDoubleSpinBox, model: QAbstractTableModel, index: QModelIndex) -> None:
        """Set the table model's data to match the editor's data."""
        data = editor.value()
        model.setData(index, data, Qt.EditRole)


class ScientificNotationDelegate(QStyledItemDelegate):
    """ScientificNotationDelegate is a QStyledItemDelegate to display a
    QLineEdit on a table.

    The delegate has a validator to allow the user to only enter an int
    or float in scientific or fixed-point notation. The notation and
    precision used by the user is tracked and used for future values.

    Parameters
    ----------
    parent : QTableView
        The delegate's associated QTableView.
    """
    def __init__(self, parent: QTableView) -> None:
        super().__init__(parent)
        self.editor_list = []

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """Create a new persistent editor on the Table View at the given index."""
        if index.row() >= len(self.editor_list):
            self.parent().openPersistentEditor(index)
            editor = self.editor_list[-1][0]
            editor.deselect()
        return super().paint(painter, option, index)

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QLineEdit:
        """Initialize a QLineEdit to delete the table's row."""
        if index.row() >= len(self.editor_list):
            value = index.data(Qt.DisplayRole)
            if value is None:
                value = self.range[0]

            rx = QRegExp("^[+-]?\d*(?:\.\d*(?:[eE][+-]?\d+)?)?$")
            validator = QRegExpValidator(rx, parent)

            editor = QLineEdit(parent)
            editor.setValidator(validator)
            editor.editingFinished.connect(lambda: self.commitData.emit(editor))

            # List containing the editor, scientific notation flag, and precision
            self.editor_list.append([editor, False, -1])
            return editor
        return super().createEditor(parent, option, index)

    def destroyEditor(self, editor: QLineEdit, index: QModelIndex) -> None:
        """Close the persistent editor for a defined index."""
        if index.row() < len(self.editor_list):
            del self.editor_list[index.row()]
            editor.deleteLater()
            self.parent().closePersistentEditor(index)
            return
        return super().destroyEditor(editor, index)

    def setEditorData(self, editor: QLineEdit, index: QModelIndex) -> None:
        """Set the editor's data to match the table model's data."""
        value = index.data(Qt.DisplayRole)

        _, sci_not, prec = self.editor_list[index.row()]
        if prec != -1:
            value = f"{value:.{prec}{'e' if sci_not else 'f'}}"
        else:
            value = str(value)

        editor.setText(value)

    def setModelData(self, editor: QLineEdit, model: QAbstractTableModel, index: QModelIndex) -> None:
        """Set the table model's data to match the editor's data."""
        text = editor.text().lower()

        sci_not = "e" in text
        if "." not in text:
            prec = 0
        elif sci_not:
            prec = text.index("e") - text.index(".") - 1
        else:
            prec = len(text) - text.index(".") - 1
        self.editor_list[index.row()][1:] = [sci_not, prec]

        data = float(text)
        model.setData(index, data, Qt.EditRole)
