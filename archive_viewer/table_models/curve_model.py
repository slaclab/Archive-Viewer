from typing import (Any, List, Dict, Optional)
from qtpy.QtGui import QColor
from qtpy.QtCore import (QObject, QModelIndex, Qt, Slot)
from pydm.widgets.baseplot import BasePlot, BasePlotCurveItem
from pydm.widgets.archiver_time_plot import ArchivePlotCurveItem
from pydm.widgets.archiver_time_plot_editor import PyDMArchiverTimePlotCurvesModel
from config import logger
from widgets import ColorButton
from table_models import ArchiverAxisModel
from qtpy import sip

class ArchiverCurveModel(PyDMArchiverTimePlotCurvesModel):
    """Model used for storing and editing archiver time plot curves.

    Parameters
    ----------
    parent (optional) : QObject
        The parent object for the table model.
    plot : BasePlot
        The plotting widget that the curves will be displayed on.
    axis_model : ArchiverAxisModel
        The table model that stores the axes for the plot.
    """

    def __init__(self, parent: Optional[QObject], plot: BasePlot, axis_model: ArchiverAxisModel) -> None:
        super(ArchiverCurveModel, self).__init__(plot, parent)
        # Remove columns for bar width, limits, and thresholds. Bar graph plot style is unused
        self._column_names = self._column_names[:6] + ("Style",) + self._column_names[6:10] + ("Hidden", "",)
        self._row_names = []
        self._axis_model = axis_model
        self._axis_model.remove_curve.connect(self.remove_curve)
        self.checkable_cols.add(self.getColumnIndex("Hidden"))
        self.append()

    def __contains__(self, key: str) -> bool:
        """Check if the given key is a channel that already exists in the model.
        Allows for the use of the 'in' keyword.

        Parameters
        ----------
        key : str
            Channel to check existence of

        Returns
        -------
        bool
            If the channel already exists in the model
        """
        return key in [curve.address for curve in self._plot._curves]

    def get_data(self, column_name: str, curve: ArchivePlotCurveItem) -> Any:
        """Get data from the model based on column name.

        Parameters
        ----------
        column_name : str
            The type of data that should be returned. Should be a name
            of one of the model's columns.
        curve : ArchivePlotCurveItem
            The curve that data should be returned for.
        """
        if column_name == "Style":
            if curve.stepMode in ["right", "left", "center"]:
                return "Step"
            elif not curve.stepMode:
                return "Direct"
        if column_name == "Hidden":
            return not curve.isVisible()
        return super(ArchiverCurveModel, self).get_data(column_name, curve)

    def set_data(self, column_name: str, curve: ArchivePlotCurveItem, value: Any) -> bool:
        """Set data on the input curve for the given name and value.

        Parameters
        ----------
        column_name : str
            The type of data that should be returned. Should be a name
            of one of the model's columns.
        curve : ArchivePlotCurveItem
            The curve that data should be returned for.
        value : Any
            The new value that the curve's data should be set to.

        Returns
        -------
        bool
            If the data was successfully set.
        """
        logger.debug(f"Setting {column_name} data for curve {curve.address}")
        ret_code = False
        index = self.index(self._plot._curves.index(curve),0)
        if sip.isdeleted(curve):
            return False
        if column_name == "Channel":
            curve.show()
            if not curve.name():
                curve.setData(name=str(value))
            if value == curve.address:
                return True

            logger.debug(f"Disconnecting old channel(s): {curve.address}")
            [ch.disconnect() for ch in curve.channels() if ch]
            curve.address = str(value)
            logger.debug(f"Connecting new channel(s): {curve.address}")
            [ch.connect() for ch in curve.channels() if ch]


            if value and self._plot._curves[-1] is curve:
                self.append()

            ret_code = True
        elif column_name == "Y-Axis Name":
            # If we change the Y-Axis, unlink from previous and link to new
            if value == curve.y_axis_name:
                return True
            self.plot.plotItem.unlinkDataFromAxis(curve)
            self.plot.linkDataToAxis(curve, value)
            ret_code = super(ArchiverCurveModel, self).set_data(column_name, curve, value)
            # Link to correct axis and unhide if necessary
            if curve.isVisible():
                self.plot.plotItem.axes[curve.y_axis_name]["item"].show()
        elif column_name == "Style":
            curve.stepMode = value
            ret_code = True
        elif column_name == "Hidden":
            # Handle toggling hidden
            hidden = bool(value)
            if hidden:
                curve.hide()
                self._axis_model.plot.plotItem.autoVisible(curve.y_axis_name)
            else:
                curve.show()
                self._axis_model.plot.plotItem.axes[curve.y_axis_name]["item"].show()
            ret_code = True
        elif column_name == "Hidden":
            # Handle toggling hidden
            hidden = bool(value)
            if hidden:
                curve.hide()
                self._axis_model.plot.plotItem.autoVisible(curve.y_axis_name)
            else:
                curve.show()
                self._axis_model.plot.plotItem.axes[curve.y_axis_name]["item"].show()
            ret_code = True
        else:
            ret_code = super(ArchiverCurveModel, self).set_data(column_name, curve, value)
        self.plot.plotItem.autoVisible(curve.y_axis_name)
        logger.debug("Finished setting curve data")
        return ret_code

    def append(self, address: Optional[str] = None, name: Optional[str] = None, color: Optional[QColor] = None, addAxis=True) -> None:
        """Add a new curve item to plot and the data model.

        Parameters
        ----------
        address : str, optional
            The PV address that the curve should gather data from.
        name : str, optional
            The display name for the curve.
        color : QColor, optional
            The curve's color on the plot.
        """
        logger.debug("Adding new empty curve to plot")
        if addAxis:
            self._axis_model.append()
        y_axis = self._axis_model.get_axis(-1)
        if not color:
            color = ColorButton.index_color(self.rowCount())
        self._row_names.append(self.next_header())
        self.beginInsertRows(QModelIndex(), len(self._plot._curves), len(self._plot._curves))
        # By default, add a blank archivePlotCurveItem such that there's an empty row to add PVs or formulas to.
        self._plot.addYChannel(y_channel=address, name=name, color=color, useArchiveData=True, yAxisName=y_axis.name)
        self.endInsertRows()
        self._plot._curves[-1].hide()
        if self.rowCount() != 1:
            logger.debug("Hide blank Y-axis")
            self._axis_model.plot.plotItem.axes[y_axis.name]["item"].hide()
        logger.debug("Finished adding new empty curve to plot")

    def set_model_curves(self, curves: List[Dict] = []) -> None:
        """Reset model curves to given list of curve properties.

        Parameters
        ----------
        curves : List[Dict]
            List of curve properties.
        """
        logger.debug("Clearing curves model.")
        self.beginResetModel()
        self._plot.clearCurves()
        self._row_names = []

        for c in curves:
            logger.debug(f"Adding curve: {c['channel']}")
            for k, v in c.items():
                if v is None:
                    del c[k]
            c['y_channel'] = c['channel']
            del c['channel']
            self._plot.addYChannel(**c)
            self._row_names.append(self.next_header())
        self.append(addAxis=False)
        self.endResetModel()
        logger.debug("Finished setting curves model")

    def removeAtIndex(self, index: QModelIndex) -> None:
        """Removes the curve at the given table index.

        Parameters
        ----------
        index : QModelIndex
            An index in the row to be removed.
        """
        logger.debug(f"Removing curve at index {index.row()}")
        if not index.isValid() or index.row() == (self.rowCount() - 1):
            return False
        del self._row_names[index.row()]
        curve = self._plot._curves[index.row()]
        [ch.disconnect() for ch in curve.channels() if ch]
        ret = super(ArchiverCurveModel, self).removeAtIndex(index)
        if not self._plot._curves:
            self.append()
        self._plot.archive_data_received()
        self._plot.set_needs_redraw()
        self._plot.redrawPlot()
        logger.debug(f"Finished removing curve previously at index {index.row()}")
        return ret

    def headerData(self, section, orientation, role=Qt.DisplayRole) -> Any:
        """Return row header for given index"""
        if role == Qt.DisplayRole and orientation == Qt.Vertical and section < self.rowCount():
            return self._row_names[section]
        return super().headerData(section, orientation, role)

    def next_header(self) -> str:
        """Construct the string for the next row in the table based on
        the current last row.

        Returns
        -------
        str
            The string for the header for the next row.
        """
        if not self._row_names:
            return 'A'

        prev_header = self._row_names[-1]
        next_header = ""

        if prev_header == 'Z' * len(prev_header):
            return 'A' * (len(prev_header) + 1)

        inc = 1
        for i in range(len(prev_header) - 1, -1, -1):
            old_val = ord(prev_header[i]) - ord('A') + inc
            new_val = chr(old_val % 26 + ord('A'))
            next_header = new_val + next_header
            inc = 1 if prev_header[i] == 'Z' else 0

        return next_header

    def curve_at_index(self, index: QModelIndex) -> ArchivePlotCurveItem:
        """Return the curve item at the given index.

        Parameters
        ----------
        index : QModelIndex
            The table index of the requested curve.

        Returns
        -------
        ArchivePlotCurveItem
            The requested curve.
        """
        return self._plot.curveAtIndex(index)

    @Slot(object)
    def remove_curve(self, curve: BasePlotCurveItem) -> None:
        """Necessary specifically for when an axis is deleted
        To properly delete all of its connected curves

        Parameters
        ----------

        curve: BasePlotCurveItem
            The curve we want to delete from the model"""
        ind = self._plot._curves.index(curve)
        ind = self.index(ind, 0)
        self.removeAtIndex(ind)
