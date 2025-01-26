from tkinter.colorchooser import askcolor
import customtkinter as ctk

from .config import (
    COLOR_SETTINGS_WINDOW_POSITION_KEY
)
from .settings import Settings

class ColorSettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent, image_processor):
        super().__init__(parent)
        self.title("Color Settings")
        self.image_processor = image_processor

        # Восстанавливаем позицию окна
        self.restore_window_position()

        # Настраиваем обработчик закрытия окна
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Создаем словарь для хранения Entry и Button виджетов
        self.color_entries = {}
        self.color_buttons = {}

        # Создаем элементы управления для каждого цвета
        colors = {
            "Background Dark": image_processor.background_dark_color,
            "Mesh Dark": image_processor.mesh_dark_color,
            "Mesh": image_processor.mesh_color,
            "Mesh Light": image_processor.mesh_light_color,
            "Background": image_processor.background_color
        }

        for i, (name, color) in enumerate(colors.items()):
            frame = ctk.CTkFrame(self)
            frame.grid(row=i, column=0, padx=10, pady=5, sticky="ew")

            label = ctk.CTkLabel(frame, text=name)
            label.grid(row=0, column=0, padx=5)

            entry = ctk.CTkEntry(frame, width=100)
            entry.insert(0, color)
            entry.grid(row=0, column=1, padx=5)

            # Создаем StringVar для отслеживания изменений в Entry
            color_var = ctk.StringVar(value=color)
            entry.configure(textvariable=color_var)

            btn = ctk.CTkButton(
                frame,
                text="...",
                command=lambda e=entry: self.pick_color(e)
            )
            btn.grid(row=0, column=2, padx=5)

            # Сохраняем виджеты в словари
            self.color_entries[name] = entry
            self.color_buttons[name] = btn

            # Настраиваем обработчик изменения текста
            color_var.trace_add("write", lambda var, index, mode, name=name, entry=entry, btn=btn:
                self.on_color_change(name, entry, btn))

            # Устанавливаем начальный цвет кнопки
            self.update_button_color(btn, color)

        # Создаем слайдер для brightness_increase
        brightness_frame = ctk.CTkFrame(self)
        brightness_frame.grid(row=len(colors), column=0, padx=10, pady=10, sticky="ew")

        brightness_label = ctk.CTkLabel(brightness_frame, text="Brightness Increase")
        brightness_label.grid(row=0, column=0, padx=5)

        self.brightness_slider = ctk.CTkSlider(
            brightness_frame,
            from_=0,
            to=100,
            number_of_steps=100,
            command=self.on_brightness_change
        )
        self.brightness_slider.set(40)  # Значение по умолчанию
        self.brightness_slider.grid(row=0, column=1, padx=5, sticky="ew")

        self.brightness_value = ctk.CTkLabel(brightness_frame, text="40")
        self.brightness_value.grid(row=0, column=2, padx=5)

    def update_button_color(self, btn, color):
        """Обновляет цвет кнопки"""
        try:
            # Проверяем, что цвет в правильном HEX формате
            if color.startswith('#') and len(color) == 7:
                btn.configure(fg_color=color)
        except:
            pass  # Игнорируем некорректные цвета

    def on_color_change(self, name, entry, btn):
        """Обработчик изменения цвета в Entry"""
        color = entry.get()
        try:
            # Проверяем, что цвет в правильном HEX формате
            if color.startswith('#') and len(color) == 7:
                self.image_processor.update_colors(name, color)
                self.update_button_color(btn, color)
        except:
            pass  # Игнорируем некорректные цвета

    def pick_color(self, entry):
        # Используем текущий цвет как начальный для color picker
        color = askcolor(color=entry.get())
        if color[1]:  # Если цвет был выбран
            entry.delete(0, 'end')
            entry.insert(0, color[1])
            # Обновляем цвет в ImageProcessor
            for name, entry_widget in self.color_entries.items():
                if entry_widget == entry:
                    self.image_processor.update_colors(name, color[1])
                    break

    def on_brightness_change(self, value):
        self.brightness_value.configure(text=f"{int(value)}")
        self.image_processor.update_brightness(value)

    def restore_window_position(self):
        """Восстанавливает позицию окна из настроек"""
        position = Settings.get(COLOR_SETTINGS_WINDOW_POSITION_KEY)
        if position:
            try:
                x, y = map(int, position.split(','))
                # Проверяем, что позиция в пределах экрана
                screen_width = self.winfo_screenwidth()
                screen_height = self.winfo_screenheight()
                x = max(0, min(x, screen_width - 300))  # 300 - примерная ширина окна
                y = max(0, min(y, screen_height - 400))  # 400 - примерная высота окна
                self.geometry(f"+{x}+{y}")
            except:
                pass  # Используем позицию по умолчанию при ошибке

    def save_window_position(self):
        """Сохраняет текущую позицию окна в настройки"""
        x = self.winfo_x()
        y = self.winfo_y()
        Settings.set(COLOR_SETTINGS_WINDOW_POSITION_KEY, f"{x},{y}")

    def on_close(self):
        """Обработчик закрытия окна"""
        self.save_window_position()
        self.destroy()
