import pytest

from pydm.application import PyDMApplication

from main import TraceDisplay


@pytest.fixture(scope="session")
def qapp(qapp_args):
    """Fixture for a PyDMApplication app instance.

    Parameters
    ----------
    qapp_args : list
        Arguments for the QApp.

    Yields
    -------
    An instance of PyDMApplication.
    """
    # Don't pass along the default app name we get from pytest-qt otherwise PyDM will misinterpret it as a ui file name
    if "pytest-qt-qapp" == qapp_args[0]:
        qapp_args.remove("pytest-qt-qapp")

    yield PyDMApplication(use_main_window=False, *qapp_args)


@pytest.fixture(scope="class")
def qtrace(qapp):
    """Fixture for an instance of the TraceDisplay. Always uses an instance of
    PyDMApplication.

    Yields
    ------
    An instance of TraceDisplay.
    """
    yield TraceDisplay()
