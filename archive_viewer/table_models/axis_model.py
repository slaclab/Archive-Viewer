from typing import (Any, List, Dict)
from qtpy.QtCore import (Qt, QVariant, QPersistentModelIndex, QModelIndex, Signal)
from pydm.widgets.baseplot import (BasePlot, BasePlotAxisItem)
from pydm.widgets.axis_table_model import BasePlotAxesModel


class ArchiverAxisModel(BasePlotAxesModel):
    """The data model for the axes tab in the properties section. Acts
    as a go-between for the axes in a plot, and QTableView items.

    Parameters
    ----------
    plot : BasePlot
        The model's associated plot widget
    parent : QObject, optional
        The model's parent, by default None
    """
    remove_curve = Signal(object)
    def __init__(self, plot: BasePlot, parent=None) -> None:
        super().__init__(plot, parent)
        self._column_names = self._column_names + ("Hidden","",)
        self.axis_count = 0
        self.checkable_col = {self.getColumnIndex("Enable Auto Range"),
                              self.getColumnIndex("Log Mode"),
                              self.getColumnIndex("Hidden")}

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """Return flags that determine how users can interact with the items in the table"""
        flags = super().flags(index)
        if index.column() in self.checkable_col:
            flags = Qt.ItemIsEnabled | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable
        return flags

    def data(self, index: QModelIndex, role=Qt.DisplayRole) -> Any:
        """Retrieve the data from the model for a given index using the
        defined role.

        Parameters
        ----------
        index : QModelIndex
            The model's index for the data being retrieved.
        role : Qt.ItemDataRole, optional
            The role used by the view to indicate which type of data it
            needs, by default Qt.DisplayRole
        """
        if not index.isValid():
            return QVariant()
        elif role == Qt.CheckStateRole and index.column() in self.checkable_col:
            value = super().data(index, Qt.DisplayRole)
            return Qt.Checked if value else Qt.Unchecked
        elif index.column() not in self.checkable_col:
            return super().data(index, role)
        return None

    def setData(self, index: QModelIndex, value: Any, role=Qt.EditRole) -> bool:
        """Sets the model data for a given index using the defined role.

        Parameters
        ----------
        index : QModelIndex
            The model's index for the data being set.
        value : Any
            The new value for the model to store.
        role : Qt.ItemDataRole, optional
            The role used by the view to indicate if the model is being editted,
            by default Qt.EditRole
        """
        if not index.isValid():
            return QVariant()
        # Specifically the Hidden column must be affected in axis_model as opposed to elsewhere
        elif role == Qt.CheckStateRole and self._column_names[index.column()] == "Hidden":
            self.plot._axes[index.row()].setHidden(bool(value))
            return True
        elif role == Qt.CheckStateRole and index.column() in self.checkable_col:
            return super().setData(index, value, Qt.EditRole)
        elif index.column() not in self.checkable_col:
            return super().setData(index, value, role)
        return None

    def append(self, name: str = "") -> None:
        """Add an empty row to the end of the table model.

        Parameters
        ----------
        name : str
            The name for the new axis item. If none is passed in, the
            axis is named "Axis <row_count>".
        """
        if not name:
            axis_count = self.rowCount() + 1
            name = f"Axis {axis_count}"
            while name in self.plot.plotItem.axes:
                axis_count += 1
                name = f"Axis {axis_count}"
        super().append(name)
        new_axis = self.get_axis(-1)
        new_axis.setLabel(name, color="black")
        row = self.rowCount() - 1
        self.attach_range_changed(row, new_axis)

    def set_model_axes(self, axes: List[Dict]) -> None:
        """Given a list of dictionaries containing axis data, clear the
        plot's axes, and set all new axes based on the provided axis data.

        Parameters
        ----------
        axes : List[Dict]
            Axis properties to be set for all new axes on the plot
        """
        key_translate = {'minRange': "min_range",
                         'maxRange': "max_range",
                         'autoRange': "enable_auto_range",
                         'logMode': "log_mode"}
        cleaned_axes = []
        for a in axes:
            clean_a = {'name': f"New Axis {len(cleaned_axes) + 1}",
                       'orientation': "left"}
            for k, v in a.items():
                if v is None:
                    continue
                elif k in key_translate:
                    new_k = key_translate[k]
                    clean_a[new_k] = a[k]
                else:
                    clean_a[k] = a[k]
            cleaned_axes.append(clean_a)

        self.beginResetModel()
        self._plot.clearAxes()
        for a in cleaned_axes:
            self._plot.addAxis(None, **a)
        self.endResetModel()

        for row, axis in enumerate(self._plot._axes):
            self.attach_range_changed(row, axis)

    def removeAtIndex(self, index: QModelIndex) -> None:
        """Removes the axis at the given table index.

        Parameters
        ----------
        index : QModelIndex
            An index in the row to be removed.
        """
        if not index.isValid() or self.rowCount() == 1:
            return False
        axis = self.get_axis(index.row())
        while axis._curves:
            curve = axis._curves[0]
            if curve == self._plot._curves[-1] or len(self._plot._curves) == 1:
                # Reasons for us to in fact not delete this axis despite manual attempt by the user
                return
            self.remove_curve.emit(curve)
        super().removeAtIndex(index)

    def setHidden(self, axis: BasePlotAxisItem, hidden: bool) -> None:
        """Hides the axis at the given table index.

        Parameters
        ----------
        index : QModelIndex
            An index in the row to be hidde.
        """
        # Hide the axis
        axis.setHidden(shouldHide=hidden)

    def get_axis(self, index: int) -> BasePlotAxisItem:
        """Return the BasePlotAxisItem for a given row number.

        Parameters
        ----------
        index : int
            The row number of the axis item.
        """
        try:
            return self.plot._axes[index]
        except IndexError:
            return None

    def attach_range_changed(self, row: int, axis: BasePlotAxisItem) -> None:
        """Attach an axis' sigYRangeChanged signal to the model's dataChanged
        signal. This will notify the model to update to reflect new data.

        Parameters
        ----------
        row : int
            The row number of the axis. (0 based)
        axis : BasePlotAxisItem
            The axis item to be connected to the dataChanged signal.
        """
        min_col = self.getColumnIndex("Min Y Range")
        min_index = QPersistentModelIndex(self.index(row, min_col))

        max_col = self.getColumnIndex("Max Y Range")
        max_index = QPersistentModelIndex(self.index(row, max_col))

        axis.sigYRangeChanged.connect(
            lambda *_: self.dataChanged.emit(
                QModelIndex(min_index), QModelIndex(max_index)
            )
        )
