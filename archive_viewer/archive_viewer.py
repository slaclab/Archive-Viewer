from functools import partial
from qtpy.QtCore import Slot
from qtpy.QtWidgets import (QAbstractButton, QApplication)
from pydm import Display
from config import logger
from mixins import TracesTableMixin, AxisTableMixin, FileIOMixin, PlotConfigMixin
from styles import CenterCheckStyle


class ArchiveViewer(Display, TracesTableMixin, AxisTableMixin, FileIOMixin, PlotConfigMixin):
    def __init__(self, parent=None, args=None, macros=None, ui_filename=__file__.replace(".py", ".ui")) -> None:
        super(ArchiveViewer, self).__init__(parent=parent, args=args, macros=macros, ui_filename=ui_filename)

        self.ui.main_spltr.setCollapsible(0, False)
        self.ui.main_spltr.setStretchFactor(0, 1)

        self.axis_table_init()
        self.traces_table_init()
        self.plot_config_init()
        self.file_io_init()

        self.curve_delegates_init()
        self.axis_delegates_init()
        self.timespan = -1
        self.button_spans = {
            self.ui.half_min_scale_btn: 30,
            self.ui.min_scale_btn: 60,
            self.ui.hour_scale_btn: 3600,
            self.ui.week_scale_btn: 604800,
            self.ui.month_scale_btn: 2628300,
            self.ui.cursor_scale_btn: -1
        }
        self.ui.timespan_btns.buttonClicked.connect(partial(self.set_plot_timerange))

        plot_viewbox = self.ui.archiver_plot.plotItem.vb
        plot_viewbox.sigRangeChangedManually.connect(self.ui.cursor_scale_btn.click)

        app = QApplication.instance()
        app.setStyle(CenterCheckStyle())

    def file_menu_items(self) -> dict:
        """Add export & import functionality to File menu; override Display.file_menu_items"""
        return {"save": (self.export_save_file, "Ctrl+S"),
                "load": (self.import_save_file, "Ctrl+L")}

    @Slot(QAbstractButton)
    def set_plot_timerange(self, button: QAbstractButton) -> None:
        """Slot to be called when a timespan setting button is pressed.
        This will enable autoscrolling along the x-axis and disable mouse
        controls. If the "Cursor" button is pressed, then autoscrolling is
        disabled and mouse controls are enabled.

        Parameters
        ----------
        button : QAbstractButton
            The timespan setting button pressed. Determines which timespan
            to set.
        """
        if button not in self.button_spans:
            logger.error(f"{button} is not a valid timespan button")
            return
        enable_scroll = button != self.ui.cursor_scale_btn
        self.timespan = self.button_spans[button]
        self.autoScroll(enable=enable_scroll)