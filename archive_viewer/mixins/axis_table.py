from qtpy.QtCore import Slot
from table_models import ArchiverAxisModel


class AxisTableMixin:
    """Mixins class for the Axes tab of the settings section."""
    def axis_table_init(self):
        """Initializer for the Axis Table Model and Table View."""
        self.axis_table_model = ArchiverAxisModel(self.ui.archiver_plot, self)
        self.axis_table_model.append()

        self.ui.time_axis_tbl.setModel(self.axis_table_model)

        self.ui.add_axis_row_btn.clicked.connect(self.addAxis)
        self.ui.del_axis_row_btn.clicked.connect(self.removeSelectedAxis)

    def axis_delegates_init(self):
        # TODO: Initialize and set all ItemDelegates for displaying
        #       widgets on the Axis table
        pass

    @Slot()
    def addAxis(self):
        self.axis_table_model.append()

    @Slot()
    def removeSelectedAxis(self):
        self.axis_table_model.removeAtIndex(self.ui.time_axis_tbl.currentIndex())
