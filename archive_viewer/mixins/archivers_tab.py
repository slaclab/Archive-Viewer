from typing import Dict
from config import archiver_urls
from widgets import CheckboxDelegate
from table_models import ArchiversTableModel


class ArchiversTabMixin:
    """Mixins class for managing the Archivers tab of the settings section."""
    def archivers_tab_init(self):
        """Initializer for Archivers Table Model and Table View."""
        self.archivers_table_model = ArchiversTableModel(self, archiver_urls)
        self.ui.archivers_tbl.setModel(self.archivers_table_model)

        self.archivers_delegate = CheckboxDelegate(self, self.archivers_table_model, self.ui.archivers_tbl)
        self.ui.archivers_tbl.setItemDelegateForColumn(0, self.archivers_delegate)

        self.ui.add_archiver_btn.clicked.connect(self.archivers_table_model.add_empty_row)

    def active_archivers(self) -> Dict[str, str]:
        """Returns a list of which archivers the user has enabled."""
        return self.archivers_table_model.get_active_archivers()
