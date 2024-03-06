import pytest
from qtpy.QtWidgets import QApplication
from archive_viewer.archive_viewer import ArchiveViewer


@pytest.fixture
def app(qtbot):
    test_app = QApplication([])
    yield test_app
    test_app.quit()


def test_archive_viewer_fetch_data_from_table(app):
    ArchiveViewer()
