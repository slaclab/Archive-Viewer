import argparse
from typing import Tuple, List, Dict
from qtpy.QtCore import Slot
from qtpy.QtWidgets import (QAbstractButton, QApplication)
from pydm import Display
from config import logger
from av_file_convert import PathAction
from mixins import (TracesTableMixin, AxisTableMixin, FileIOMixin)
from styles import CenterCheckStyle


class ArchiveViewer(Display, TracesTableMixin, AxisTableMixin, FileIOMixin):
    def __init__(self, parent=None, args=None, macros=None, ui_filename=__file__.replace(".py", ".ui")) -> None:
        super(ArchiveViewer, self).__init__(parent=parent, args=args,
                                            macros=macros, ui_filename=ui_filename)
        # Set up PyDMApplication
        self.configure_app()

        # Initialize the Mixins
        self.axis_table_init()
        self.traces_table_init()
        self.file_io_init()

        self.curve_delegates_init()
        self.axis_delegates_init()

        # Create reference dict for timespan_btns button group
        self.button_spans = {self.ui.half_min_scale_btn: 30,
                             self.ui.min_scale_btn: 60,
                             self.ui.hour_scale_btn: 3600,
                             self.ui.week_scale_btn: 604800,
                             self.ui.month_scale_btn: 2628300,
                             self.ui.cursor_scale_btn: -1}
        self.ui.timespan_btns.buttonClicked.connect(self.set_plot_timerange)

        # Click "Cursor" button on plot-mouse interaction
        plot_viewbox = self.ui.archiver_plot.plotItem.vb
        plot_viewbox.sigRangeChangedManually.connect(self.ui.cursor_scale_btn.click)

        # Parse macros & arguments, then include them in startup
        input_file, startup_pvs = self.parse_macros_and_args(macros, args)
        if input_file:
            self.import_save_file(input_file)
        for pv in startup_pvs:
            if pv in self.curves_model:
                continue
            self.curves_model.add_curve(pv)

    def menu_items(self) -> dict:
        """Add export & import functionality to File menu"""
        return {"Export": (self.export_save_file, "Ctrl+S"),
                "Import": (self.import_save_file, "Ctrl+L")}

    def configure_app(self):
        """UI changes to be made to the PyDMApplication"""
        app = QApplication.instance()

        # Hide navigation bar by default (can be shown in menu bar)
        app.main_window.toggle_nav_bar(False)
        app.main_window.ui.actionShow_Navigation_Bar.setChecked(False)

        # Hide status bar by default (can be shown in menu bar)
        app.main_window.toggle_status_bar(False)
        app.main_window.ui.actionShow_Status_Bar.setChecked(False)

        # Add style to center checkboxes in table cells
        app.setStyle(CenterCheckStyle())

        # Adjust settings for main_spltr
        self.ui.main_spltr.setCollapsible(0, False)
        self.ui.main_spltr.setStretchFactor(0, 1)

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

        enable_scroll = (button != self.ui.cursor_scale_btn)
        timespan = self.button_spans[button]

        self.ui.archiver_plot.setAutoScroll(enable_scroll, timespan)

    def parse_macros_and_args(self, macros: Dict[str, str | list], args: List[str]) -> Tuple[str, list]:
        """Parse user provided macros and args into lists of PVs to use on
        startup or which file to import on startup

        Parameters
        ----------
        macros : Dict[str, str | list]
            Dictionary containing all of the macros passed into PyDM
        args : List[str]
            List of all arguments passed into the application to be parsed

        Returns
        -------
        tuple
            A tuple containing the file to import from and the list of PVs to use on startup
        """
        # Default macros is None
        if not macros:
            macros = {}

        # Construct an argument parser for args
        trace_parser = argparse.ArgumentParser(description="Trace\nThis is a PyDM application "
                                               + "used to display archived and live pv data.",
                                               formatter_class=argparse.RawTextHelpFormatter)
        trace_parser.add_argument("-i", "--input_file",
                                  action=PathAction,
                                  type=str,
                                  default="",
                                  help="Absolute file path to import from;\n"
                                  + "Alternatively can be provided as INPUT_FILE macro")
        trace_parser.add_argument("-p", "--pvs",
                                  type=str,
                                  nargs='*',
                                  default=[],
                                  help="List of PVs to show on startup;\n"
                                       + "Alternatively can be provided as PV or PVS macros")

        # Parse arguments and ignore unknowns
        trace_args, unknown = trace_parser.parse_known_args(args)
        if unknown:
            logger.warning(f"Not using unknown arguments: {unknown}")

        # Get the file to import from if one is provided. Prioritize args over macro
        input_file = trace_args.input_file
        if not input_file and 'INPUT_FILE' in macros:
            input_file = macros['INPUT_FILE']

        # Get the list of PVs to show on startup
        startup_pvs = []
        for key in ("PV", "PVS"):
            if key in macros:
                val = macros[key]
                if isinstance(val, str):
                    startup_pvs.append(val)
                elif isinstance(val, list):
                    startup_pvs += val
        startup_pvs += trace_args.pvs

        # Remove duplicates from startup_pvs
        startup_pvs = list(dict.fromkeys(startup_pvs))

        return (input_file, startup_pvs)
