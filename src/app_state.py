import customtkinter as ctk
from src.config import (
    APPEARANCE_MODE_LIGHT, APPEARANCE_MODE_KEY,
    MIRROR_EFFECT_ENABLED, MIRROR_EFFECT_KEY,
    SHOW_CAMERA, SHOW_CAMERA_KEY,
    FULLSCREEN_ALERT_ENABLED, FULLSCREEN_ALERT_KEY,
    STRABISMUS_THRESHOLD, STRABISMUS_THRESHOLD_KEY,
    OVERLAY_COLOR, OVERLAY_COLOR_KEY,
    OVERLAY_OPACITY, OVERLAY_OPACITY_KEY
)
from src.settings import Settings

class AppState:
    """Класс для хранения состояния приложения"""

    def __init__(self):
        """Инициализация состояния приложения"""
        # Инициализация переменных состояния с привязкой к Settings
        self.mirror_effect = self._create_var_with_trace(
            ctk.BooleanVar,
            MIRROR_EFFECT_KEY,
            MIRROR_EFFECT_ENABLED
        )
        self.show_camera = self._create_var_with_trace(
            ctk.BooleanVar,
            SHOW_CAMERA_KEY,
            SHOW_CAMERA
        )
        self.fullscreen_alert = self._create_var_with_trace(
            ctk.BooleanVar,
            FULLSCREEN_ALERT_KEY,
            FULLSCREEN_ALERT_ENABLED
        )
        self.threshold_value = self._create_var_with_trace(
            ctk.DoubleVar,
            STRABISMUS_THRESHOLD_KEY,
            STRABISMUS_THRESHOLD
        )
        self.overlay_color = self._create_var_with_trace(
            ctk.StringVar,
            OVERLAY_COLOR_KEY,
            OVERLAY_COLOR
        )
        self.overlay_opacity = self._create_var_with_trace(
            ctk.IntVar,
            OVERLAY_OPACITY_KEY,
            OVERLAY_OPACITY
        )
        self.light_theme = self._create_var_with_trace(
            ctk.BooleanVar,
            APPEARANCE_MODE_KEY,
            APPEARANCE_MODE_LIGHT
        )
        # Динамическое значение, не требует сохранения
        self.eye_distance = ctk.StringVar(value="0.000")

    def _create_var_with_trace(self, var_class, settings_key, default_value):
        """Создает переменную с привязкой к Settings"""
        var = var_class(value=Settings.get(settings_key, default_value))
        var.trace_add('write', lambda *args: Settings.set(settings_key, var.get()))
        return var
