from typing import (Any, List, Dict, Optional)
from qtpy.QtGui import QColor
from qtpy.QtCore import (QObject, QModelIndex, Qt)
from pydm.widgets.baseplot import BasePlot, BasePlotCurveItem
from pydm.widgets.archiver_time_plot import ArchivePlotCurveItem, FormulaCurveItem
from pydm.widgets.archiver_time_plot_editor import PyDMArchiverTimePlotCurvesModel
from functools import partial
import re
from widgets import ColorButton
from table_models import ArchiverAxisModel
from config import logger


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
        self._column_names = self._column_names[:6] + ("Style",) + self._column_names[6:] + ("",)
        self._row_names = []
        self._axis_model = axis_model

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
            return curve.plot_style
        return super(ArchiverCurveModel, self).get_data(column_name, curve)

    def set_data(self, column_name: str, curve: BasePlotCurveItem, value: Any) -> bool:
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
        ret_code = False
        if column_name == "Channel":
            # If we are changing the channel, then we need to check the current type, and the type we're going to
            index = self.index(self._plot._curves.index(curve),0)
            value_is_formula = value.startswith("f://")
            curve_is_formula = isinstance(curve, FormulaCurveItem)
            if value_is_formula and not curve_is_formula:
                # Regardless of starting point, going to a formula is handled in this one function
                return self.replaceToFormula(index = index, formula = value)
            elif value_is_formula and curve_is_formula:
                try:
                    pv_dict = self.formulaToPVDict(index, value)
                except ValueError as e:
                    logger.error(e)

                curve.formula = value
                curve.pvs = pv_dict
            elif not value_is_formula and not curve_is_formula:
                if value == curve.address:
                    return True
                [ch.disconnect() for ch in curve.channels() if ch]
                curve.address = str(value)
                [ch.connect() for ch in curve.channels() if ch]
            else:
                self.replaceToArchivePlot(curve = curve, index = index, address = str(value))

            if not curve.name():
                curve.setData(name=str(value))

            if value and self._plot._curves[-1] is curve:
                if self.rowCount() != 1:
                    self._axis_model.append()
                y_axis = self._axis_model.get_axis(-1)
                row = self.rowCount()
                col = self._column_names.index("Y-Axis Name")
                index = self.index(row, col)
                self.setData(index, y_axis.name)
                self.plot.linkDataToAxis(curve, y_axis.name)
                self.append()
            ret_code = True
        elif column_name == "Style":
            curve.plot_style = str(value)
            ret_code = True
        else:
            ret_code = super(ArchiverCurveModel, self).set_data(column_name, curve, value)
        #After messing with the data, just cleanly redraw everything
        self._plot.requestDataFromArchiver()
        self._plot.set_needs_redraw()
        self._plot.redrawPlot()
        return ret_code

    def append(self, address: Optional[str] = None, name: Optional[str] = None, color: Optional[QColor] = None) -> None:
        """Add a new curve item to plot and the data model.

        Parameters
        ----------
        address : str, optional
            The PV address that the curve should gather data from.
        name : str, optional
            The display name for the curve.
        color : Optional[QColor], optional
            The curve's color on the plot.
        """
        if self.rowCount() == 0:
            self._axis_model.append()
        y_axis = self._axis_model.get_axis(-1)
        if not color:
            color = ColorButton.index_color(self.rowCount())
        self._row_names.append(self.next_header())
        #          KLYS:LI22:31:KVAC
        self.beginInsertRows(QModelIndex(), len(self._plot._curves), len(self._plot._curves))
        #by default, add a blank archivePlotCurveItem such that there's an empty row to add PVs or formulas to.
        self._plot.addYChannel(y_channel=address, name=name, color=color, useArchiveData=True, yAxisName=y_axis.name)
        self.endInsertRows()

    def set_model_curves(self, curves: List[Dict]) -> None:
        self.beginResetModel()
        self._plot.clearCurves()
        self._row_names = []

        for c in curves:
            for k, v in c.items():
                if v is None:
                    del c[k]
            c['y_channel'] = c['channel']
            del c['channel']
            self._plot.addYChannel(**c)
            self._row_names.append(self.next_header())
        self.append()

        self.endResetModel()

    def replaceToArchivePlot(self, curve: BasePlotCurveItem, index: QModelIndex, address: str, color: Optional[QColor] = None):
        y_axis = y_axis = self._axis_model.get_axis(index.row())
        # saving the next line for axis fixes
        # self.plot.plotItem.axes[self.get_data(curve=self._plot._curves[index.row()], column_name="Y-Axis Name")]
        # Get rid of the old formula
        self.plot.plotItem.unlinkDataFromAxis(curve.y_axis_name)
        self.plot.removeItem(curve)
        if not color:
            color = ColorButton.index_color(index.row())
        # Create a new ArchivePlotCurveItem and link it
        self._plot._curves[index.row()] = self._plot.replaceToArchivePlot(address=address, name=address, color=color, yAxisName=y_axis.name)
        self.plot.linkDataToAxis(self._plot._curves[index.row()], y_axis.name)
        del curve

    def formulaToPVDict(self, rowName: str, formula: str) -> dict:
        pvs = re.findall("{(.+?)}", formula)
        pvdict = dict()
        for pv in pvs:
            # Check if all of the requested rows actually exist
            if pv not in self._row_names:
                raise ValueError(f"{pv} is an invalid variable name")
            elif pv == rowName:
                raise ValueError(f"{pv} is recursive")
            else:
                # if it's good, add it to the dictionary of curves. rindex = row index (int) as opposed to index, which is a QModelIndex
                rindex = self._row_names.index(pv)
                pvdict[pv] = self._plot._curves[rindex]
        return pvdict

    def replaceToFormula(self, index: QModelIndex, formula: str, color: Optional[QColor] = None) -> bool:
        """Replaces existing ArchivePlotCurveItem with a new FormulaCurveItem

        Parameters
        ----------
        formula : str
            The Formula we want to graph
        name : str, optional
            The display name for the curve.
        color : Optional[QColor], optional
            The curve's color on the plot.
        """
        # Find row headers using regex

        rowName = self._row_names[index.row()]
        pvdict = self.formulaToPVDict(rowName, formula)
        if pvdict == None:
            return False
        curve = self._plot._curves[index.row()]
        if not color:
            color = ColorButton.index_color(index.row())
        #          KLYS:LI22:31:KVAC
        # Handle Archives and formulas differently
        if index.row() == self.rowCount() - 1:
            self.append()
        y_axis = self._axis_model.get_axis(index.row())
        self._plot._curves[index.row()] = self._plot.addFormulaChannel(formula=formula, name=formula, pvs=pvdict,color=color, useArchiveData=True, yAxisName=y_axis.name)
        self._plot._curves[index.row()].formula_invalid_signal.connect(partial(self.invalidFormula, header = rowName))
        # Need to check if Formula is referencing a dead row
        self.plot.plotItem.unlinkDataFromAxis(curve.y_axis_name)
        self.plot.removeItem(curve)
        # Disconnect everything and delete it, create a new Formula with the dictionary of curve
        [ch.disconnect() for ch in curve.channels() if ch]
        del curve
        return True

    def invalidFormula(self, header):
        # handling row deletion if the formula is no longer valid
        rindex = self._row_names.index(header)
        index = self.index(rindex,0)
        if not index.isValid() or index.row() == (self.rowCount() - 1):
            return False
        del self._row_names[index.row()]
        curve = self._plot._curves[rindex]
        self.beginRemoveRows(QModelIndex(), index.row(), index.row())
        if curve.y_axis_name in self._plot.plotItem.axes:
            self.plot.plotItem.unlinkDataFromAxis(curve.y_axis_name)
        self.plot.removeItem(curve)
        self.plot._curves.remove(curve)
        self.endRemoveRows()
        if not self._plot._curves:
            self.append()
        del curve
        # Prompt a redraw top cascade and delete any consequential formulas
        self._plot.archive_data_received()
        self._plot.set_needs_redraw()
        self._plot.redrawPlot()

    def removeAtIndex(self, index: QModelIndex) -> None:
        """Removes the curve at the given table index.

        Parameters
        ----------
        index : QModelIndex
            An index in the row to be removed.
        """
        if isinstance(self._plot._curves[index.row()], FormulaCurveItem):
            # Formula Curves don't have channel ddata so we should just remove it as if it were no longer valid
            self.invalidFormula(self._row_names[index.row()])
            return False

        if not index.isValid() or index.row() == (self.rowCount() - 1):
            return False
        del self._row_names[index.row()]
        ret = super(ArchiverCurveModel, self).removeAtIndex(index)
        if not self._plot._curves:
            self.append()
        self._plot.archive_data_received()
        self._plot.set_needs_redraw()
        self._plot.redrawPlot()
        return ret

    def headerData(self, section, orientation, role=Qt.DisplayRole) -> Any:
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
