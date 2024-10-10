from datetime import datetime, timedelta


def test_defaults(qtrace):
    """Ensure that TraceDisplay's default values are set correctly.

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing

    Expectations
    ------------
    All of the application's values are in an expected state.
    """
    # Timespan buttons: '1h' button should be checked
    assert qtrace.ui.timespan_btns.checkedButton() is qtrace.ui.hour_scale_btn

    # Check plot's timespan will be set to 1 hour immediately after init
    axis_range = [datetime.fromtimestamp(int(r)) for r in qtrace.ui.main_plot.getXAxis().range]
    assert axis_range[1] - axis_range[0] == timedelta(hours=1)

    # Curve model should have one hidden curve
    assert qtrace.curves_model.rowCount() == 1
    assert len(qtrace.ui.main_plot._curves) == 1

    # Axis model should have one axis
    assert len(qtrace.ui.main_plot._axes) == 1
    assert qtrace.axis_table_model.rowCount() == 1

    # Plot Config default values
    assert qtrace.ui.plot_title_edit.text() == ""
    assert qtrace.ui.x_grid_chckbx.isChecked() is False
    assert qtrace.ui.y_grid_chckbx.isChecked() is False
    assert qtrace.ui.legend_chckbx.isChecked() is False
    assert qtrace.ui.xafs_spnbx.value() == 12
    assert qtrace.ui.refresh_interval_spnbx.value() == 5
    assert qtrace.background_color_button.color.name() == "#ffffff"
    assert qtrace.mouse_mode_cmbbx.currentIndex() == 0
    assert qtrace.opacity_sldr.value() == 50
    assert qtrace.crosshair_chckbx.isChecked() is False


def test_parse_macros_and_args(qtrace):
    pass


def test_git_version(qtrace):
    pass


def test_reset_plot(qtrace):
    pass


def test_set_plot_timerange(qtrace):
    pass
