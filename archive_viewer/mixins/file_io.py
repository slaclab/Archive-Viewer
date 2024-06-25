from os import getenv
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
from qtpy.QtWidgets import (QMessageBox, QFileDialog)
from config import (logger, save_file_dir)
from av_file_convert import ArchiveViewerFileConverter


class FileIOMixin:
    def file_io_init(self):
        self.converter = ArchiveViewerFileConverter()

        self.io_path = save_file_dir

        self.ui.test_export_btn.clicked.connect(self.export_save_file)
        self.ui.test_import_btn.clicked.connect(self.import_save_file)

    def export_save_file(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Archive Viewer",
                                                   str(self.io_path),
                                                   "Python Archive Viewer (*.pyav)")
        file_name = Path(file_name)
        if file_name.is_dir():
            logger.warning("No file name provided")
            return

        try:
            self.io_path = file_name.parent
            self.converter.export_file(file_name, self.ui.archiver_plot)
        except FileNotFoundError as e:
            logger.error(e)
            self.export_save_file()

    def import_save_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Archive Viewer",
                                                   str(self.io_path),
                                                   "Python Archive Viewer (*.pyav);;"
                                                   + "Java Archive Viewer (*.xml);;"
                                                   + "All Files (*)")
        file_name = Path(file_name)
        if not file_name.is_file():
            return

        try:
            file_data = self.converter.import_file(file_name)
            if self.converter.import_is_xml():
                file_data = self.converter.convert_data(file_data)
            self.io_path = file_name.parent
        except FileNotFoundError as e:
            logger.error(e)
            self.import_save_file()
            return

        import_url = urlparse(file_data['archiver_url'])
        archiver_url = urlparse(getenv("PYDM_ARCHIVER_URL"))
        if import_url.hostname != archiver_url.hostname:
            ret = QMessageBox.warning(self,
                                      "Import Error",
                                      "The config file you tried to open reads from a different archiver.\n"
                                      f"\nCurrent archiver is:\n{archiver_url.hostname}\n"
                                      f"\nAttempted import uses:\n{import_url.hostname}",
                                      QMessageBox.Ok | QMessageBox.Cancel,
                                      QMessageBox.Ok)
            if ret == QMessageBox.Cancel:
                return

        self.axis_table_model.set_model_axes(file_data['y-axes'])
        self.curves_model.set_model_curves(file_data['curves'])
