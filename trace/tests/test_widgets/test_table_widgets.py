import pytest
from qtpy.QtGui import QColor
from qtpy.QtCore import Qt

from widgets import table_widgets
from widgets.table_widgets import ColorButton

DEF_COLOR = QColor("black")


TEST_PALETTE = [
    QColor(255, 0, 0),  # Red
    QColor(0, 255, 0),  # Green
    QColor(0, 0, 255),  # Blue
]


@pytest.fixture(scope="class")
def color_btn(qapp):
    """Fixture for an instance of the ColorButton. Sets the button's default color.

    Yields
    ------
    An instance of ColorButton with color & default set to DEF_COLOR
    """
    yield ColorButton(color=DEF_COLOR)


@pytest.mark.parametrize("test_color", [*TEST_PALETTE])
def test_color_change(qtbot, color_btn, test_color):
    """Test that setting the button's color does change the button's color,
    stylesheet, and emit the color_change signal.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget test
    color_btn : fixture
        The current instance of ColorButton
    test_color : QColor

    Expectations
    ------------
    The object's color and styleSheet should reflect the change, and the
    color_change signal should have emitted the new color.
    """
    # Check that the color_change signal is emitted
    with qtbot.waitSignal(color_btn.color_changed, timeout=100) as blocker:
        color_btn.color = test_color

    assert color_btn.color == test_color
    assert color_btn.styleSheet() == "ColorButton {background-color: " + test_color.name() + "};"
    assert blocker.args == [test_color]


def test_color_no_change(qtbot, color_btn):
    """Test that setting the button's color to the value it's already set to
    does not emit the color_change signal.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget test
    color_btn : fixture
        The current instance of ColorButton

    Expectations
    ------------
    The ColorButton instance should not emit any signal and should not change.
    """
    # Check that the color_change signal is not emitted
    with qtbot.waitSignal(color_btn.color_changed, raising=False, timeout=100) as blocker:
        color_btn.color = DEF_COLOR

    assert blocker.args is None


def test_right_click(qtbot, color_btn):
    """Set the ColorButton's color to something new, then right click the button.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget test
    color_btn : fixture
        The current instance of ColorButton

    Expectations
    ------------
    The ColorButton's color should change back to it's initial color.
    """
    # Set the button's color to red
    color_btn.color = QColor("red")
    assert color_btn.color != DEF_COLOR

    # Right click the button and confirm it is set to its default color
    qtbot.addWidget(color_btn)
    qtbot.mouseClick(color_btn, Qt.RightButton)
    assert color_btn.color == DEF_COLOR


@pytest.mark.parametrize(
    "random_values, expected_hsl",
    [
        ([0.1, 0.5, 0.6], (36, 192, 133)),
        ([0.9, 0.3, 0.4], (324, 166, 122)),
    ],
)
def test_random_color(monkeypatch, random_values, expected_hsl):
    """Test that ColorButton.random_color correctly generates a color based on
    random values.

    Parameters
    ----------
    monkeypatch : fixture
        To override table_widgets.color_palette
    random_values : tuple
        List of "randomly" generated values used to determine the colors HSL
    expected_hsl : tuple
        List of expected HSL values to be returned

    Expectations
    ------------
    Returned color should have the same hue, saturation, and lightness as the
    expected values
    """

    # Mock the random() function to return the predefined random values sequentially
    def mock_random():
        return random_values.pop(0)

    monkeypatch.setattr(table_widgets, "random", mock_random)

    # Get the predetermined "random" color
    color = ColorButton.random_color()
    hue, saturation, lightness, _ = color.getHsl()

    # Assert that the HSL values match the expected color's values
    assert hue == expected_hsl[0]
    assert saturation == expected_hsl[1]
    assert lightness == expected_hsl[2]


@pytest.mark.parametrize(
    "index, expected_base_color, expected_dark_factor",
    [
        (0, TEST_PALETTE[0], 100),  # Index 0 -> first color, no darkening
        (3, TEST_PALETTE[0], 135),  # Index 3 -> first color, one level of darkening
        (5, TEST_PALETTE[2], 135),  # Index 5 -> third color, one level of darkening
        (7, TEST_PALETTE[1], 170),  # Index 7 -> second color, two levels of darkening
    ],
)
def test_index_color(monkeypatch, index, expected_base_color, expected_dark_factor):
    """Tests ColorButton.index_color() by setting the color palette to an expected
    palette, passing an index to be set, and checking that the returned value matches
    the expected value.

    Parameters
    ----------
    monkeypatch : fixture
        To override table_widgets.color_palette
    index : int
        Index to be passed to ColorButton.index_color
    expected_base_color : QColor
        The base of the color expected to be returned
    expected_dark_factor : int
        The factor to which the expected color should be darkened

    Expectations
    ------------
    The color returned by index_color matches the expected base color and
    darkness factor
    """
    monkeypatch.setattr(table_widgets, "color_palette", TEST_PALETTE)

    # Call the static method and calculate expected darker color
    color = ColorButton.index_color(index)
    expected_color = expected_base_color.darker(expected_dark_factor)

    assert color == expected_color
