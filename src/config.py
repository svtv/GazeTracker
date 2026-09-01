## User-Specific Constants
APP_TITLE = "Eye and Face Tracker"
APP_FONT = "Segoe UI"
APP_FONT_KEY = 'app.font'
APP_FONT_SIZE = 13
APP_FONT_SIZE_TITLE = 16

# Semantic UI colors. Each tuple contains (Light, Dark).
# Most widget colors live in themes/clinical_luxury.json; these values are for
# third-party widgets and data/status colors that CustomTkinter does not theme.
DATA_ACCENT_COLOR = ("#397FA5", "#68B4D2")
THRESHOLD_COLOR = ("#9C6946", "#E0A06F")
CAMERA_LETTERBOX_COLOR = "#151A1D"

# Main window size
APP_GEOMETRY = "980x600"
APP_GEOMETRY_KEY = 'app.geometry'
APP_MINSIZE_WIDTH = 800
APP_MINSIZE_HEIGHT = 600

# Overlay window
OVERLAY_COLOR = "#ff0000"  # Red
OVERLAY_COLOR_KEY = 'app.overlay_color'
OVERLAY_OPACITY = 64
OVERLAY_OPACITY_KEY = 'app.overlay_opacity'

# Loading window size
LOADING_WINDOW_WIDTH = 400
LOADING_WINDOW_HEIGHT = 240
LOADING_WINDOW_GEOMETRY = f"{LOADING_WINDOW_WIDTH}x{LOADING_WINDOW_HEIGHT}"

# Settings window size
SETTINGS_WINDOW_WIDTH = 300
SETTINGS_WINDOW_HEIGHT = 200
SETTINGS_WINDOW_GEOMETRY = f"{SETTINGS_WINDOW_WIDTH}x{SETTINGS_WINDOW_HEIGHT}"

# Window position setting key
MAIN_WINDOW_POSITION_KEY = 'app.window_position'
LOADING_WINDOW_POSITION_KEY = 'app.loading_window_position'
SETTINGS_WINDOW_POSITION_KEY = 'app.settings_window_position'
COLOR_SETTINGS_WINDOW_POSITION_KEY = 'app.color_settings_window_position'

# Threshold knob configuration
THRESHOLD_KNOB_STEP = 0.010
THRESHOLD_KNOB_STEP_PRECISE = 0.001

# Show camera configuration
SHOW_CAMERA = False
SHOW_CAMERA_KEY = 'app.show_camera'

# Mirror effect configuration
MIRROR_EFFECT_ENABLED = True  # Is the mirror effect enabled by default?
MIRROR_EFFECT_KEY = 'app.mirror_effect'  # Key for saving the setting

# Fullscreen alert configuration
FULLSCREEN_ALERT_ENABLED = True  # Is the fullscreen alert enabled by default?
FULLSCREEN_ALERT_KEY = 'app.fullscreen_alert'  # Key for saving the setting

STRABISMUS_RANGE_MIN = 0.45
STRABISMUS_RANGE_MAX = 0.55
STRABISMUS_THRESHOLD = 0.50
STRABISMUS_THRESHOLD_KEY = 'strabismus.threshold'

## Display Configuration

# REFRESH_DELAY_MS: Delay in milliseconds between each frame refresh
REFRESH_DELAY_MS = 50

# Temporal stabilization of detected face landmarks. Lower values are
# smoother but react more slowly to intentional movement.
LANDMARK_SMOOTHING_ALPHA = 0.20

# Stabilization of the measured ratio and threshold alert state.
RATIO_SMOOTHING_ALPHA = 0.25
ALERT_HYSTERESIS = 0.005
ALERT_CONFIRMATION_FRAMES = 3

# CHART_BUFFER_SIZE: Size of the buffer for the line chart
CHART_BUFFER_SIZE = 100

# Display settings
SHOW_DISTANCE = True
SHOW_DISTANCE_KEY = 'app.show_distance'

# Eye display settings
EYES_DISPLAY_SCALE = 2.0  # Масштаб отображения глаз
EYES_DISPLAY_SCALE_KEY = 'display.eyes_scale'
EYES_VERTICAL_OFFSET = 0  # Смещение глаз по вертикали (-1 до 1, где 0 - центр)
EYES_VERTICAL_OFFSET_KEY = 'display.eyes_vertical_offset'

# Enhanced eye display
EYE_STYLE = {
    'PUPIL_SCALE': 0.35,  # Размер зрачка относительно радиуса глаза
    'IRIS_THICKNESS': 0.15,  # Толщина радужки относительно радиуса
    'HIGHLIGHT_SCALE': 0.2,  # Размер блика относительно радиуса
    'HIGHLIGHT_OFFSET': 0.25,  # Смещение блика относительно радиуса
    'MESH_LINE_SCALE': 0.08,  # Толщина линий меша относительно масштаба
    'POINT_SCALE': 0.1,  # Размер точек относительно масштаба
}

# Detailed eye settings
IRIS_DETAIL_LEVEL = 3  # Количество колец в радужке (1-5)
IRIS_OUTER_COLOR = "#4EA6C8"  # Внешний цвет радужки
IRIS_INNER_COLOR = "#10283A"  # Внутренний цвет радужки (зрачок)
IRIS_HIGHLIGHT_COLOR = "#D9F3F8"  # Цвет бликов
IRIS_HIGHLIGHT_SIZE = 0.2  # Размер блика относительно радиуса (0-1)
IRIS_HIGHLIGHT_OFFSET = 0.3  # Смещение блика относительно радиуса (0-1)

# Eyebrow settings
EYEBROW_THICKNESS = 1.2  # Толщина бровей относительно базовой (0.5-2)
EYEBROW_SMOOTHING = True  # Сглаживание бровей

# Line settings
LINE_THICKNESS = 0.7  # Толщина линий относительно масштаба (0.3-1.5)
LINE_SMOOTHING = True  # Сглаживание линий

# Diagnostic-view palettes. Unlike the camera image, the generated tracking
# view follows the application appearance mode.
TRACKING_PALETTE_DARK = {
    "background": "#173A52",
    "background_dark": "#10283A",
    "mesh": "#4EA6C8",
    "mesh_light": "#8DD3E8",
    "mesh_dark": "#204A62",
    "status_text": "#9CCBD9",
}

TRACKING_PALETTE_LIGHT = {
    "background": "#A7B2BC",
    "background_dark": "#929FAA",
    "mesh": "#285474",
    "mesh_light": "#668DA9",
    "mesh_dark": "#18364D",
    "status_text": "#294A63",
}

# Backward-compatible aliases for code that imports individual colors.
BACKGROUND_COLOR = TRACKING_PALETTE_DARK["background"]
BACKGROUND_DARK_COLOR = TRACKING_PALETTE_DARK["background_dark"]
MESH_COLOR = TRACKING_PALETTE_DARK["mesh"]
MESH_LIGHT_COLOR = TRACKING_PALETTE_DARK["mesh_light"]
MESH_DARK_COLOR = TRACKING_PALETTE_DARK["mesh_dark"]
TEXT_COLOR = "#D9F3F8"
IRIS_COLOR = "#F6E27F"  # RGB(246, 226, 127)
EYE_INNER_CORNER_COLOR = "#A30B37"  # RGB(163, 11, 55)
EYE_OUTER_CORNER_COLOR = "#A30B37"  # RGB(163, 11, 55)

# Active color scheme (change these values to switch between themes)
# BACKGROUND_COLOR = BACKGROUND_COLOR_DARK
# BACKGROUND_DARK_COLOR = BACKGROUND_DARK_COLOR_DARK
# MESH_COLOR = MESH_COLOR_DARK
# MESH_DARK_COLOR = MESH_DARK_COLOR_DARK
# MESH_LIGHT_COLOR = MESH_LIGHT_COLOR_DARK

# Цвета для особых состояний
STRABISMUS_DETECTED_COLOR = "#FF0000"  # Красный
YELLOW_COLOR = "#FFFF00"  # Желтый для текста "No face detected"
RED_COLOR = "#A30B37"  # RGB(163, 11, 55)
RED_LIGHT_COLOR = "#F8A0B9"  # RGB(248, 160, 185)

# DEFAULT_WEBCAM: Default camera source index. '0' usually refers to the built-in webcam.
DEFAULT_WEBCAM = 0

## Head Pose Estimation Landmark Indices
# These indices correspond to the specific facial landmarks used for head pose estimation.
LEFT_EYE_IRIS = [474, 475, 476, 477]  # Left eye iris
RIGHT_EYE_IRIS = [469, 470, 471, 472]  # Right eye iris
LEFT_EYE_OUTER_CORNER = [33]  # Left eye outer corner
LEFT_EYE_INNER_CORNER = [133]  # Left eye inner corner
RIGHT_EYE_OUTER_CORNER = [362]  # Right eye outer corner
RIGHT_EYE_INNER_CORNER = [263]  # Right eye inner corner
RIGHT_EYE_POINTS = [33, 160, 159, 158, 133, 153, 145, 144]  # Right eye points
LEFT_EYE_POINTS = [362, 385, 386, 387, 263, 373, 374, 380]  # Left eye points
NOSE_TIP_INDEX = 4  # Nose tip index
CHIN_INDEX = 152  # Chin index
LEFT_EYE_LEFT_CORNER_INDEX = 33  # Left eye left corner index
RIGHT_EYE_RIGHT_CORNER_INDEX = 263  # Right eye right corner index
LEFT_MOUTH_CORNER_INDEX = 61  # Left mouth corner index
RIGHT_MOUTH_CORNER_INDEX = 291  # Right mouth corner index

## MediaPipe Model Confidence Parameters
# These thresholds determine how confidently the model must detect or track to consider the results valid.
MIN_DETECTION_CONFIDENCE = 0.8  # Minimum detection confidence
MIN_DETECTION_CONFIDENCE_KEY = 'model.min_detection_confidence'
MIN_TRACKING_CONFIDENCE = 0.8  # Minimum tracking confidence
MIN_TRACKING_CONFIDENCE_KEY = 'model.min_tracking_confidence'

# Iris and eye corners landmarks indices
LEFT_IRIS = [474, 475, 476, 477]  # Left iris
RIGHT_IRIS = [469, 470, 471, 472]  # Right iris
L_H_LEFT = [33]  # Left eye left corner
L_H_RIGHT = [133]  # Left eye right corner
R_H_LEFT = [362]  # Right eye left corner
R_H_RIGHT = [263]  # Right eye right corner

# Face Selected points indices for Head Pose Estimation | Индексы выбранных точек лица для определения положения головы
HEAD_INDICES_POSE = [1, 33, 61, 199, 263, 291]

# Theme configuration
APPEARANCE_MODE_KEY = 'app.appearance_mode'
APPEARANCE_MODE_LIGHT = False
