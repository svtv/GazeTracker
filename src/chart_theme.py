"""Theme switching adapter for CTkChart 2.2.1.

CTkChart maintains its own polling theme manager. Its default theme-change path
replays all retained data from a background thread, which makes a live chart
jump and also calls Tk outside the GUI thread. This adapter synchronizes that
manager immediately and recolors existing canvas items without moving them.
"""
from ctkchart.ThemeManager import ThemeManager as CTkChartThemeManager


def prepare_chart_theme(appearance_mode):
    """Prevent CTkChart's polling thread from replaying data for this switch."""
    CTkChartThemeManager.theme = appearance_mode


def recolor_chart(chart, appearance_mode, background_color, color_pairs):
    """Change chart colors in place while preserving data and coordinates."""
    color_index = 0 if appearance_mode == "Light" else 1
    replacements = {}
    for light_color, dark_color in color_pairs:
        target_color = (light_color, dark_color)[color_index]
        replacements[light_color.lower()] = target_color
        replacements[dark_color.lower()] = target_color

    # Public configure() changes only widget surfaces for these properties and
    # does not replay line data.
    chart.configure(
        axis_color=background_color,
        bg_color=background_color,
        fg_color=background_color,
    )

    # CTkChart does not expose its plot canvas publicly. This private attribute
    # is stable in the pinned 2.2.1 dependency and keeps the workaround local.
    canvas = chart._CTkLineChart__output_canvas  # pylint: disable=protected-access
    for item_id in canvas.find_all():
        current_color = canvas.itemcget(item_id, "fill")
        replacement = replacements.get(current_color.lower())
        if replacement is not None and replacement != current_color:
            canvas.itemconfigure(item_id, fill=replacement)
