from widgets import ColorButton
from pyqtgraph import ViewBox


class PlotConfigMixin:
    def plot_config_init(self):
        self.plot = self.ui.archiver_plot
        self.ui.plot_title_edit.textChanged.connect(self.plot.setPlotTitle)

        self.ui.x_grid_chckbx.clicked.connect(self.show_x_grid)

        self.ui.y_grid_chckbx.clicked.connect(self.show_y_grid)

        self.ui.opacity_sldr.valueChanged.connect(self.change_opacity)

        background_color_button = ColorButton(color="white")
        self.ui.background_color_lyt.insertWidget(1, background_color_button)
        background_color_button.color_changed.connect(self.plot.setBackgroundColor)

        self.ui.refresh_interval_spnbx.setValue(5)
        self.ui.refresh_interval_spnbx.valueChanged.connect(lambda interval: self.autoScroll(enable=True))

        self.ui.legend_chckbx.clicked.connect(self.plot.setShowLegend)

        self.ui.crosshair_chckbx.clicked.connect(lambda show: self.plot.enableCrosshair(show, 100, 100))

        self.ui.mouse_mode_cmbbx.currentIndexChanged.connect(self.changeMouseMode)

    def changeMouseMode(self, mode:int):
        mouse_mode = ViewBox.RectMode
        if mode == 1:
            mouse_mode = ViewBox.PanMode
        self.plot.plotItem.getViewBox().setMouseMode(mouse_mode)

    def autoScroll(self, enable: bool = False):
        refresh_interval = int(self.ui.refresh_interval_spnbx.value() * 1000)
        self.plot.setAutoScroll(enable=enable, timespan=self.timespan, refresh_rate=refresh_interval)

    def change_opacity(self, opacity: int):
        x_visible = self.ui.x_grid_chckbx.isChecked()
        y_visible = self.ui.y_grid_chckbx.isChecked()

        opacity /= 100.0
        self.plot.setShowXGrid(x_visible, opacity)
        self.plot.setShowYGrid(y_visible, opacity)

    def show_x_grid(self, visible: bool):
        opacity = self.ui.opacity_sldr.value() / 100.0
        self.plot.setShowXGrid(visible, opacity)

    def show_y_grid(self, visible: bool):
        opacity = self.ui.opacity_sldr.value() / 100.0
        self.plot.setShowYGrid(visible, opacity)
