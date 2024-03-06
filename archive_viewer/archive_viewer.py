from time import time
from qtpy.QtCore import Slot
from pydm import Display
from mixins import (TracesTableMixin, AxisTableMixin, ArchiversTabMixin)


class ArchiveViewer(Display, TracesTableMixin, AxisTableMixin, ArchiversTabMixin):
    def __init__(self, parent=None, args=None, macros=None, ui_filename=__file__.replace(".py", ".ui")):
        super(ArchiveViewer, self).__init__(parent=parent, args=args,
                                            macros=macros, ui_filename=ui_filename)

        self.ui.main_spltr.setCollapsible(0, False)
        self.ui.main_spltr.setStretchFactor(0, 1)

        self.axis_table_init()
        self.traces_table_init()
        self.archivers_tab_init()

        self.curve_delegates_init()
        self.axis_delegates_init()

        self.ui.half_min_scale_btn.clicked.connect(lambda _: self.set_plot_timerange(30))
        self.ui.min_scale_btn.clicked.connect(lambda _: self.set_plot_timerange(60))
        self.ui.hour_scale_btn.clicked.connect(lambda _: self.set_plot_timerange(3600))
        self.ui.week_scale_btn.clicked.connect(lambda _: self.set_plot_timerange(604800))
        self.ui.month_scale_btn.clicked.connect(lambda _: self.set_plot_timerange(2628300))
        self.ui.auto_scale_btn.toggled.connect(self.ui.archiver_plot.setAutoRangeY)

    @Slot(float)
    def set_plot_timerange(self, timespan: float) -> None:
        """Sets the Archiver Plot's x-axis to show the requested timespan.

        Parameters
        ----------
        timespan : float
            The number of seconds to show on the plot.
        """
        curr = time()
        self.ui.archiver_plot.plotItem.setXRange(curr - timespan, curr)
