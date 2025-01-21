import json
import os
from typing import Any, Dict

from .config import (
    APP_FONT, APP_FONT_KEY,
    APP_GEOMETRY, APP_GEOMETRY_KEY,
    OVERLAY_COLOR, OVERLAY_COLOR_KEY,
    OVERLAY_OPACITY, OVERLAY_OPACITY_KEY,
    SHOW_CAMERA, SHOW_CAMERA_KEY,
    MIRROR_EFFECT_ENABLED, MIRROR_EFFECT_KEY,
    FULLSCREEN_ALERT_ENABLED, FULLSCREEN_ALERT_KEY,
    STRABISMUS_THRESHOLD, STRABISMUS_THRESHOLD_KEY
)

class Settings:
    """
    Singleton class for managing application settings
    """
    _instance = None
    _settings: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance._load_settings()
        return cls._instance

    def _load_settings(self):
        """Loads settings from JSON file. Creates empty settings if file doesn't exist"""
        settings_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'settings.json')

        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                self._settings = json.load(f)
        except FileNotFoundError:
            self._settings = self._create_default_settings()

    def get(self, path: str, default: Any = None) -> Any:
        """
        Gets setting value by path in format 'section.subsection.key'
        Example: settings.get('app.geometry')
        """
        try:
            value = self._settings
            for key in path.split('.'):
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, path: str, value: Any) -> None:
        """
        Sets setting value and saves to file only if:
        1. Path doesn't exist in settings
        2. Value at specified path differs from new value
        """
        # Check current value
        current_value = self.get(path)

        # If value is the same - don't save
        if current_value == value:
            return

        # If value is different or doesn't exist - update
        keys = path.split('.')
        current = self._settings

        # Go through all keys except the last one
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Set the value
        current[keys[-1]] = value

        # Save to file
        settings_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'settings.json')
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(self._settings, f, indent=4)

    @property
    def all(self) -> Dict[str, Any]:
        """Returns all settings"""
        return self._settings.copy()

    @staticmethod
    def _create_default_settings() -> Dict[str, Any]:
        """Creates dictionary with default settings from config.py"""
        # List of key-value pairs from config.py
        settings_pairs = [
            (APP_FONT_KEY, APP_FONT),
            (APP_GEOMETRY_KEY, APP_GEOMETRY),
            (OVERLAY_COLOR_KEY, OVERLAY_COLOR),
            (OVERLAY_OPACITY_KEY, OVERLAY_OPACITY),
            (SHOW_CAMERA_KEY, SHOW_CAMERA),
            (MIRROR_EFFECT_KEY, MIRROR_EFFECT_ENABLED),
            (FULLSCREEN_ALERT_KEY, FULLSCREEN_ALERT_ENABLED),
            (STRABISMUS_THRESHOLD_KEY, STRABISMUS_THRESHOLD),
        ]

        # Build settings dictionary from pairs
        default_settings = {}
        for key, value in settings_pairs:
            current = default_settings
            key_parts = key.split('.')
            for part in key_parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[key_parts[-1]] = value

        return default_settings
