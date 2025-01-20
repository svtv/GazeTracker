## User-Specific Constants
APP_TITLE = "Eye and Face Tracker"
APP_FONT = "Segoe UI"
APP_FONT_KEY = 'app.font'
APP_FONT_SIZE = 13
APP_FONT_SIZE_TITLE = 16

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

# Threshold knob configuration
THRESHOLD_KNOB_STEP = -0.010
THRESHOLD_KNOB_STEP_PRECISE = -0.001

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
REFRESH_DELAY_MS = 100

# CHART_BUFFER_SIZE: Size of the buffer for the line chart
CHART_BUFFER_SIZE = 100

# BACKGROUND_COLOR: BGR tuple for the background color (default is dark gray)
BACKGROUND_COLOR = (64, 64, 64)  # Dark gray
# BACKGROUND_COLOR = (128, 128, 128)  # Medium gray
# BACKGROUND_COLOR = (32, 32, 32)  # Very dark gray
# BACKGROUND_COLOR = (96, 96, 96)  # Gray

TEXT_COLOR = (0, 0, 255)  # Red (BGR)
MESH_COLOR = (0, 255, 0)  # Green (BGR)
IRIS_COLOR = (255, 0, 255)  # Purple (BGR)
EYE_INNER_CORNER_COLOR = (255, 255, 255)  # White (BGR)
EYE_OUTER_CORNER_COLOR = (255, 255, 0)  # Cyan (BGR)

STRABISMUS_DETECTED_COLOR = (255, 0, 0)  # Blue (BGR)

# Color scheme 1
BACKGROUND_COLOR = (59, 7, 0)
MESH_COLOR = (210, 194, 51)
IRIS_COLOR = (247, 221, 7)

# Color scheme 2
BACKGROUND_COLOR = (12, 41, 81)
TEXT_COLOR = (65, 106, 165)
MESH_COLOR = (32, 204, 224)
IRIS_COLOR = (187, 223, 221)
EYE_INNER_CORNER_COLOR = (242, 250, 229)
EYE_OUTER_CORNER_COLOR = (226, 164, 141)

# Color scheme https://coolors.co/0c2951-46aafe-f6e27f-a30b37-a9fff7
# generated from BACKGROUND_COLOR = (12, 41, 81)
BACKGROUND_COLOR = (12, 41, 81)
BACKGROUND_DARK_COLOR = (8, 27, 53)
# BACKGROUND_DARK_COLOR = (11, 36, 71)
TEXT_COLOR = (169, 255, 247)
MESH_COLOR = (70, 170, 254)
MESH_LIGHT_COLOR = (174, 218, 255)
MESH_DARK_COLOR = (1, 112, 203)
IRIS_COLOR = (246, 226, 127)
EYE_INNER_CORNER_COLOR = (163, 11, 55)
EYE_OUTER_CORNER_COLOR = (226, 164, 141)
YELLOW_COLOR = (246, 226, 127)
RED_COLOR = (163, 11, 55)
RED_LIGHT_COLOR = (248, 160, 185)

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
