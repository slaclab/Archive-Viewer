from typing import Tuple
from datetime import datetime

from pyqtgraph import ViewBox
from qtpy.QtCore import Slot, QDateTime
from qtpy.QtWidgets import QHeaderView

from config import logger
from widgets import ComboBoxDelegate, DeleteRowDelegate, ScientificNotationDelegate
from table_models import ArchiverAxisModel


class AxisTableMixin:
    """Mixins class for the Axes tab of the settings section."""

    def axis_table_init(self) -> None:
        """Initializer for the Axis Table Model and Table View."""
        self.axis_table_model = ArchiverAxisModel(self.ui.main_plot, self)
        self.ui.time_axis_tbl.setModel(self.axis_table_model)

        hdr = self.ui.time_axis_tbl.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.Stretch)
        del_col = self.axis_table_model.getColumnIndex("")
        hdr.setSectionResizeMode(del_col, QHeaderView.ResizeToContents)

        plot_viewbox = self.ui.main_plot.plotItem.vb
        plot_viewbox.sigXRangeChanged.connect(self.set_axis_datetimes)
        plot_viewbox.sigRangeChangedManually.connect(lambda *_: self.set_axis_datetimes())

        self.ui.main_start_datetime.dateTimeChanged.connect(lambda qdt: self.set_time_axis_range((qdt, None)))
        self.ui.main_end_datetime.dateTimeChanged.connect(lambda qdt: self.set_time_axis_range((None, qdt)))

        self.ui.add_axis_row_btn.clicked.connect(self.addAxis)

    def axis_delegates_init(self) -> None:
        """Initialize and set the ItemDelegates for the axis table."""
        orientation_col = self.axis_table_model.getColumnIndex("Y-Axis Orientation")
        orientation_map = {"Left": "left", "Right": "right"}
        orientation_del = ComboBoxDelegate(self.ui.time_axis_tbl, orientation_map)
        self.ui.time_axis_tbl.setItemDelegateForColumn(orientation_col, orientation_del)

        min_range_col = self.axis_table_model.getColumnIndex("Min Y Range")
        min_range_del = ScientificNotationDelegate(self.ui.time_axis_tbl)
        self.ui.time_axis_tbl.setItemDelegateForColumn(min_range_col, min_range_del)

        max_range_col = self.axis_table_model.getColumnIndex("Max Y Range")
        max_range_del = ScientificNotationDelegate(self.ui.time_axis_tbl)
        self.ui.time_axis_tbl.setItemDelegateForColumn(max_range_col, max_range_del)

        delete_col = self.axis_table_model.getColumnIndex("")
        delete_row_del = DeleteRowDelegate(self.ui.time_axis_tbl)
        self.ui.time_axis_tbl.setItemDelegateForColumn(delete_col, delete_row_del)

    @Slot(object)
    def set_time_axis_range(self, raw_range: Tuple[QDateTime, QDateTime] = (None, None)) -> None:
        """PyQT Slot to set the plot's X-Axis range. This slot should be
        triggered on QDateTimeEdit value change.

        Parameters
        ----------
        raw_range : Tuple[QDateTime], optional
            Takes in a tuple of 2 values, where one is a QDateTime and
            the other is None. The positioning changes either the plot's
            min or max range value. By default (None, None)
        """
        # Disable Autoscroll if enabled
        self.ui.cursor_scale_btn.click()

        proc_range = [None, None]
        for ind, val in enumerate(raw_range):
            # Values that are QDateTime are converted to a float timestamp
            if isinstance(val, QDateTime):
                proc_range[ind] = val.toSecsSinceEpoch()
            # Values that are None use the existing range value
            elif not val:
                proc_range[ind] = self.ui.main_plot.getXAxis().range[ind]
        proc_range.sort()

        logger.debug(f"Setting plot's X-Axis range to {proc_range}")
        self.ui.main_plot.plotItem.vb.blockSignals(True)
        self.ui.main_plot.plotItem.setXRange(*proc_range, padding=0)
        self.ui.main_plot.plotItem.vb.blockSignals(False)

    @Slot(object, object)
    def set_axis_datetimes(self, _: ViewBox = None, time_range: Tuple[float, float] = None) -> None:
        """Slot used to update the QDateTimeEdits on the Axis tab. This
        slot is called when the plot's X-Axis range changes values.

        Parameters
        ----------
        _ : ViewBox, optional
            The ViewBox on which the range is changing. This is unused
        time_range : Tuple[float, float], optional
            The new range values for the QDateTimeEdits, by default None
        """
        if not time_range:
            time_range = self.ui.main_plot.getXAxis().range
        if min(time_range) <= 0:
            return

        time_range = [datetime.fromtimestamp(f) for f in time_range]

        edits = (self.ui.main_start_datetime, self.ui.main_end_datetime)
        for ind, qdt in enumerate(edits):
            if qdt.hasFocus():
                continue
            qdt.blockSignals(True)
            qdt.setDateTime(QDateTime(time_range[ind]))
            qdt.blockSignals(False)

    @Slot()
    def addAxis(self) -> None:
        """Slot for button to add a new row to the axis table."""
        self.axis_table_model.append()
