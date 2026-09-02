from src.chart_theme import (
    CTkChartThemeManager,
    prepare_chart_theme,
    recolor_chart,
)


class FakeCanvas:
    def __init__(self):
        self.colors = {1: "#397FA5", 2: "#C9DDE5", 3: "#9C6946"}

    def find_all(self):
        return tuple(self.colors)

    def itemcget(self, item_id, option):
        assert option == "fill"
        return self.colors[item_id]

    def itemconfigure(self, item_id, **options):
        self.colors[item_id] = options["fill"]


class FakeChart:
    def __init__(self):
        self._CTkLineChart__output_canvas = FakeCanvas()
        self.configuration = None

    def configure(self, **options):
        self.configuration = options


def test_prepare_chart_theme_synchronizes_ctkchart_tracker():
    prepare_chart_theme("Light")

    assert CTkChartThemeManager.theme == "Light"


def test_recolor_chart_preserves_items_and_uses_dark_colors():
    chart = FakeChart()
    pairs = (
        ("#397FA5", "#68B4D2"),
        ("#9C6946", "#E0A06F"),
        ("#C9DDE5", "#294956"),
    )

    recolor_chart(chart, "Dark", "#171A1D", pairs)

    assert chart.configuration == {
        "axis_color": "#171A1D",
        "bg_color": "#171A1D",
        "fg_color": "#171A1D",
    }
    assert chart._CTkLineChart__output_canvas.colors == {
        1: "#68B4D2",
        2: "#294956",
        3: "#E0A06F",
    }
