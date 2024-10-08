import pytest

from widgets.archive_search import ArchiveSearchWidget


@pytest.fixture(scope="class")
def search_wid(qapp):
    """Fixture for an instance of the ArchiveSearchWidget.

    Yields
    ------
    An instance of ArchiveSearchWidget.
    """
    yield ArchiveSearchWidget()


def test_archive_search(search_wid):
    pass


def test_drag_action(search_wid):
    pass


def test_insert_pvs(search_wid):
    pass
