from pydm.widgets.axis_table_model import BasePlotAxesModel


class ArchiverAxisModel(BasePlotAxesModel):
    """The data model for the axes tab in the properties section. Acts
    as a go-between for the axes in a plot, and QTableView items.
    """
    def append(self, name: str = ""):
        """Add an empty row to the end of the table model."""
        if not name:
            axis_count = self.rowCount() + 1
            name = f"New Axis {axis_count}"
            while name in self._plot.plotItem.axes:
                axis_count += 1
                name = f"New Axis {axis_count}"

        super().append(name)
