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
    STRABISMUS_THRESHOLD, STRABISMUS_THRESHOLD_KEY,
    APPEARANCE_MODE_KEY, APPEARANCE_MODE_LIGHT
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

    def get_settings(self) -> Dict[str, Any]:
        """Returns the settings dictionary"""
        return self._settings

    def update_settings(self, settings: Dict[str, Any]):
        """Updates the settings dictionary"""
        self._settings = settings

    @classmethod
    def get(cls, path: str, default: Any = None) -> Any:
        """
        Gets setting value by path in format 'section.subsection.key'
        Example: Settings.get('app.geometry')
        """
        if cls._instance is None:
            cls()

        try:
            value = cls._instance.get_settings()
            for key in path.split('.'):
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    @classmethod
    def set(cls, path: str, value: Any) -> None:
        """
        Sets setting value and saves to file only if:
        1. Path doesn't exist in settings
        2. Value at specified path differs from new value
        """
        if cls._instance is None:
            cls()

        # Check current value
        current_value = cls.get(path)

        # If value is the same - don't save
        if current_value == value:
            return

        # If value is different or doesn't exist - update
        keys = path.split('.')
        settings = cls._instance.get_settings().copy()
        current = settings

        # Go through all keys except the last one
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Set the value
        current[keys[-1]] = value

        # Update settings
        cls._instance.update_settings(settings)

        # Save to file
        settings_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'settings.json')
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(cls._instance.get_settings(), f, indent=4)

    @classmethod
    def all(cls) -> Dict[str, Any]:
        """Returns all settings"""
        if cls._instance is None:
            cls()
        return cls._instance.get_settings().copy()

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
            (APPEARANCE_MODE_KEY, APPEARANCE_MODE_LIGHT),
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
