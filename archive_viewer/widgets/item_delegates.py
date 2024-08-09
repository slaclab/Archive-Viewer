from abc import abstractmethod
from typing import (Union, Tuple)
from qtpy.QtGui import (QColor, QPainter, QRegExpValidator)
from qtpy.QtCore import (Qt, QEvent, QPoint, Slot, Signal, QRegExp,
                         QAbstractTableModel, QModelIndex, QAbstractItemModel)
from qtpy.QtWidgets import (QStyledItemDelegate, QComboBox, QStyle, QPushButton,
                            QTableView, QStyleOptionViewItem, QWidget,
                            QDoubleSpinBox, QLineEdit)
from widgets import ColorButton


class EditorDelegate(QStyledItemDelegate):
    """Abstract Base Class for QStyledItemDelegates that display a persistent
    editor. When inheriting from this class, make sure to override abstract
    methods: createEditor, setEditorData, setModelData

    Parameters
    ----------
    parent : QTableView
        The QTableView associated with the delegate. Used for opening
        persistent editors.
    """
    def __init__(self, parent: QTableView) -> None:
        super().__init__(parent)
        self.editor_list = []
        model = self.parent().model()
        model.modelAboutToBeReset.connect(self.reset_editors)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """Create a new persistent editor on the Table View at the given index.

        Parameters
        ----------
        painter : QtGui.QPainter
            The Qt Painter used to display the delegate's editors
        option : QtWidgets.QStyleOptionViewItem
            The style option used to render the item
        index : QModelIndex
            The index to display the editor on
        """
        if index.row() == len(self.editor_list):
            self.parent().openPersistentEditor(index)
        return super().paint(painter, option, index)

    @abstractmethod
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        """Editor creator function to be overridden by subclasses.

        Parameters
        ----------
        parent : QWidget
            The parent widget intended to be used as the parent of the new editor
        option : QStyleOptionViewItem
            The item options used in creating the editor
        index : QModelIndex
            The index to display the editor on

        Returns
        -------
        QWidget
            The QWidget editor for the specified index
        """
        return super().createEditor(parent, option, index)

    def destroyEditor(self, editor: QWidget, index: QModelIndex) -> None:
        """Close the persistent editor for a defined index.

        Parameters
        ----------
        editor : QWidget
            The editor to be destroyed
        index : QModelIndex
            The index of the editor to be destroyed
        """
        if index.row() < len(self.editor_list):
            del self.editor_list[index.row()]
            editor.deleteLater()
            self.parent().closePersistentEditor(index)
            return
        return super().destroyEditor(editor, index)

    @abstractmethod
    def setEditorData(self, editor: QWidget, index: QModelIndex) -> None:
        """Abstract method to be overridden by subclasses. Sets the
        delegate's editor to match the table model's data.

        Parameters
        ----------
        editor : QWidget
            The editor which will need to be set. Changes type based on
            how the subclass is implemented.
        index : QModelIndex
            The index of the editor to be changed.
        """
        return super().setEditorData(editor, index)

    @abstractmethod
    def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex) -> None:
        """Abstract method to be overridden by subclasses. Sets the
        table's model data to match the delegate's editor.

        Parameters
        ----------
        editor : QWidget
            The editor containing the data to be saved in the model. Changes
            type based on how the subclass is implemented.
        model : QAbstractItemModel
            The model which will need to be set.
        index : QModelIndex
            The index of the editor to be changed.
        """
        return super().setModelData(editor, model, index)

    @Slot()
    def reset_editors(self) -> None:
        """Slot called when the delegate's model will be reset. Closes all
        persistent editors in the delegate.
        """
        for editor in self.editor_list:
            editor_pos = editor.pos()
            index = self.parent().indexAt(editor_pos)

            editor.deleteLater()
            self.parent().closePersistentEditor(index)
        self.editor_list = []


class ColorButtonDelegate(EditorDelegate):
    """ColorButtonDelegate is a QStyledItemDelegate to display a persistent
    QPushButton widget on a QTableView that allow's the user to change an object's color.

    Parameters
    ----------
    parent : QTableView
        The parent object for the ColorButtonDelegate. Should be the
        associated QTableView
    """
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> ColorButton:
        """Initialize a ColorButton for use in the Table View.

        Parameters
        ----------
        parent : QWidget
            The parent widget intended to be used as the parent of the new editor
        option : QStyleOptionViewItem
            The item options used in creating the editor
        index : QModelIndex
            The index to display the editor on

        Returns
        -------
        ColorButton
            The ColorButton editor for the specified index
        """
        if index.row() >= len(self.editor_list):
            value = index.data(Qt.DisplayRole)
            editor = ColorButton(parent, color=value)
            editor.color_changed.connect(lambda: self.commitData.emit(editor))

            self.editor_list.append(editor)
            return editor
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor: ColorButton, index: QModelIndex) -> None:
        """Set the editor's data to match the table model's data.

        Parameters
        ----------
        editor : ColorButton
            The editor which will need to be set.
        index : QModelIndex
            The index of the editor to be changed.
        """
        value = index.data(Qt.DisplayRole)
        editor.color = QColor(value)

    def setModelData(self, editor: ColorButton, model: QAbstractTableModel, index: QModelIndex) -> None:
        """Set the table model's data to match the editor's data.

        Parameters
        ----------
        editor : ColorButton
            The editor which will need to be set.
        model : QAbstractItemModel
            The model which will need to be set.
        index : QModelIndex
            The index of the editor to be changed.
        """
        data = editor.color.name()
        model.setData(index, data, Qt.EditRole)


class FloatDelegate(EditorDelegate):
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

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """Create a new persistent editor on the Table View at the given index.

        Parameters
        ----------
        painter : QPainter
            The Qt Painter used to display the delegate's editors
        option : QStyleOptionViewItem
            The style option used to render the item
        index : QModelIndex
            The index to display the editor on
        """
        deselect_lineEdit =  index.row() == len(self.editor_list)
        super().paint(painter, option, index)

        if deselect_lineEdit:
            editor = self.editor_list[-1]
            editor.lineEdit().deselect()

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QDoubleSpinBox:
        """Initialize a QDoubleSpinBox to delete the table's row.

        Parameters
        ----------
        parent : QWidget
            The parent widget intended to be used as the parent of the new editor
        option : QStyleOptionViewItem
            The item options used in creating the editor
        index : QModelIndex
            The index to display the editor on

        Returns
        -------
        QDoubleSpinBox
            The QDoubleSpinBox editor for the specified index
        """
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

    def setEditorData(self, editor: QDoubleSpinBox, index: QModelIndex) -> None:
        """Set the editor's data to match the table model's data.

        Parameters
        ----------
        editor : QDoubleSpinBox
            The editor which will need to be set. Changes type based on
            how the subclass is implemented.
        index : QModelIndex
            The index of the editor to be changed.
        """
        value = index.data(Qt.DisplayRole)
        editor.setValue(value)
        editor.lineEdit().deselect()

    def setModelData(self, editor: QDoubleSpinBox, model: QAbstractTableModel, index: QModelIndex) -> None:
        """Set the table model's data to match the editor's data.

        Parameters
        ----------
        editor : QDoubleSpinBox
            The editor containing the data to be saved in the model.
        model : QAbstractItemModel
            The model which will need to be set.
        index : QModelIndex
            The index of the editor to be changed.
        """
        data = editor.value()
        model.setData(index, data, Qt.EditRole)


class ScientificNotationDelegate(EditorDelegate):
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
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """Create a new persistent editor on the Table View at the given index.

        Parameters
        ----------
        painter : QPainter
            The Qt Painter used to display the delegate's editors
        option : QStyleOptionViewItem
            The style option used to render the item
        index : QModelIndex
            The index to display the editor on
        """
        deselect_lineEdit = index.row() == len(self.editor_list)
        super().paint(painter, option, index)

        if deselect_lineEdit:
            editor = self.editor_list[-1][0]
            editor.deselect()

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QLineEdit:
        """Initialize a QLineEdit to delete the table's row.

        Parameters
        ----------
        parent : QWidget
            The parent widget intended to be used as the parent of the new editor
        option : QStyleOptionViewItem
            The item options used in creating the editor
        index : QModelIndex
            The index to display the editor on

        Returns
        -------
        QLineEdit
            The QLineEdit editor for the specified index
        """
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

    def setEditorData(self, editor: QLineEdit, index: QModelIndex) -> None:
        """Set the editor's data to match the table model's data.

        Parameters
        ----------
        editor : QLineEdit
            The editor which will need to be set. Changes type based on
            how the subclass is implemented.
        index : QModelIndex
            The index of the editor to be changed.
        """
        value = index.data(Qt.DisplayRole)

        _, sci_not, prec = self.editor_list[index.row()]
        if prec != -1:
            value = f"{value:.{prec}{'e' if sci_not else 'f'}}"
        else:
            value = str(value)

        editor.setText(value)

    def setModelData(self, editor: QLineEdit, model: QAbstractTableModel, index: QModelIndex) -> None:
        """Set the table model's data to match the editor's data.

        Parameters
        ----------
        editor : QLineEdit
            The editor containing the data to be saved in the model.
        model : QAbstractItemModel
            The model which will need to be set.
        index : QModelIndex
            The index of the editor to be changed.
        """
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


class DeleteRowDelegate(EditorDelegate):
    """DeleteRowDelegate is a QStyledItemDelegate to display a persistent
    QPushButton widget on a QTableView that allow's the user to delete the row.

    Parameters
    ----------
    parent : QTableView
        The parent object for the DeleteRowDelegate. Should be the
        associated QTableView
    """
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QPushButton:
        """Initialize a QPushButton editor to delete the table's row.

        Parameters
        ----------
        parent : QWidget
            The parent widget intended to be used as the parent of the new editor
        option : QStyleOptionViewItem
            The item options used in creating the editor
        index : QModelIndex
            The index to display the editor on

        Returns
        -------
        QPushButton
            The QPushButton editor for the specified index
        """
        if index.row() >= len(self.editor_list):
            editor = QPushButton(parent)
            icon = editor.style().standardIcon(QStyle.SP_DialogCancelButton)
            editor.setIcon(icon)
            editor.setToolTip("Delete Row")
            editor.clicked.connect(lambda: self.commitData.emit(editor))

            self.editor_list.append(editor)
            return editor

        return super().createEditor(parent, option, index)

    def setModelData(self, _: QPushButton, model: QAbstractTableModel, index: QModelIndex) -> None:
        """When the setModelData slot is triggered, the row is removed.

        Parameters
        ----------
        editor : QPushButton
            The editor which is unused.
        model : QAbstractItemModel
            The model which we are removing a row from.
        index : QModelIndex
            The index of the row to be deleted.
        """
        model.removeAtIndex(index)


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
        model = self.parent().model()
        model.modelAboutToBeReset.connect(self.reset_editors)

    def initStyleOption(self, option: QStyleOptionViewItem, index: QModelIndex):
        """Initialize a QComboBox for use in the Table View.

        Parameters
        ----------
        option : QStyleOptionViewItem
            The style option used to render the QComboBox
        index : QModelIndex
            The index to display the QComboBox on
        """
        if index.row() >= len(self.editor_list):
            editor = QComboBox()

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

            editor.setFocusPolicy(Qt.StrongFocus)
            editor.setContextMenuPolicy(Qt.CustomContextMenu)
            editor.customContextMenuRequested.connect(self.combo_menu_requested)
            editor.currentIndexChanged.connect(lambda: self.commitData.emit(editor))

            self.editor_list.append(editor)
            self.parent().setIndexWidget(index, editor)
        return super().initStyleOption(option, index)

    def destroyEditor(self, editor: QComboBox, index: QModelIndex) -> None:
        """Destroy the editor for a defined index.

        Parameters
        ----------
        editor : QComboBox
            The editor to be destroyed
        index : QModelIndex
            The index of the editor to be destroyed
        """
        if index.row() < len(self.editor_list):
            self.editor_list[index.row()].deleteLater()
            del self.editor_list[index.row()]
            return
        return super().destroyEditor(editor, index)

    def setEditorData(self, editor: QComboBox, index: QModelIndex) -> None:
        """Set the editor's data to match the table model's data.

        Parameters
        ----------
        editor : QComboBox
            The editor which will need to be set. Changes type based on
            how the subclass is implemented.
        index : QModelIndex
            The index of the editor to be changed.
        """
        value = index.data(Qt.DisplayRole)
        ind = editor.findText(value)
        if ind >= 0:
            editor.setCurrentIndex(ind)

    def setModelData(self, editor: QComboBox, model: QAbstractTableModel, index: QModelIndex) -> None:
        """Set the table model's data to match the editor's data.

        Parameters
        ----------
        editor : QComboBox
            The editor containing the data to be saved in the model.
        model : QAbstractItemModel
            The model which will need to be set.
        index : QModelIndex
            The index of the data to be changed.
        """
        curr_text = editor.currentText()
        if isinstance(self.data_source, dict):
            data = self.data_source[curr_text]
        elif isinstance(self.data_source, QAbstractItemModel):
            self.sigTextChange.emit(index.row(), curr_text)
            data = curr_text
        model.setData(index, data, Qt.EditRole)

    def eventFilter(self, object: QComboBox, event: QEvent) -> bool:
        """Disable scrolling for widgets that are not the focus.

        Parameters
        ----------
        object : QComboBox
            The QComboBox that we are watching for events on.
        event : QEvent
            The events that we may want to filter out.

        Returns
        -------
        bool
            Whether or not the event is accepted by the filter.
        """
        if event.type() == QEvent.Wheel and not object.hasFocus():
            return True
        return super().eventFilter(object, event)

    @Slot()
    def reset_editors(self) -> None:
        """Slot called when the delegate's model will be reset. Closes all
        persistent editors in the delegate.
        """
        for editor in self.editor_list:
            editor_pos = editor.pos()
            index = self.parent().indexAt(editor_pos)

            editor.deleteLater()
            self.parent().closePersistentEditor(index)
        self.editor_list = []

    @Slot(QPoint)
    def combo_menu_requested(self, pos: QPoint) -> None:
        """Redirect menu requests to the Table View.

        Parameters
        ----------
        pos : QPoint
            The location of where the menu was requested.
        """
        pos = self.sender().mapToParent(pos)
        self.parent().customContextMenuRequested.emit(pos)
