"""
Overlay window for displaying visual alerts
Оверлейное окно для отображения визуальных оповещений
"""

import win32gui
import win32con
import win32api
from ctypes import windll, byref, c_int
from threading import Thread, Event, Timer
import time

class OverlayWindow:
    def __init__(self):
        """Initialize the overlay window"""
        self.should_show = False
        self.is_running = True
        self.wc = None
        self.hwnd = None
        self.brush = None
        self.close_event = Event()
        self.is_visible = False  # Флаг текущего состояния видимости
        self.window_opacity = 64  # Default window opacity
        self.window_color = (255, 0, 0)  # Default color (red)
        self.hide_timer = None  # Timer for hide delay
        self.HIDE_DELAY = 0.25  # Hide delay in seconds
        self.thread = Thread(target=self._run_window, daemon=True)
        self.thread.start()
        time.sleep(0.1)  # Wait for window creation

    def _register_window_class(self):
        """Register the overlay window class"""
        # Get module handle
        hinst = win32api.GetModuleHandle(None)
        if not hinst:
            print("Failed to get module handle")
            return
        
        # Register window class
        wc = win32gui.WNDCLASS()
        wc.hInstance = hinst
        wc.lpfnWndProc = self._window_proc
        wc.lpszClassName = "GazeTrackerOverlay"
        wc.style = win32con.CS_HREDRAW | win32con.CS_VREDRAW
        
        try:
            atom = win32gui.RegisterClass(wc)
            if atom:
                self.wc = wc
        except Exception as e:
            # Class might already be registered
            pass

    def _create_overlay_window(self):
        """Create a transparent overlay window"""
        if not self.wc:
            self._register_window_class()

        # Get screen dimensions
        screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)

        # Extended window styles for transparency and click-through
        ex_style = (
            win32con.WS_EX_LAYERED |      # For transparency
            win32con.WS_EX_TRANSPARENT |   # Click-through
            win32con.WS_EX_TOPMOST |       # Always on top
            win32con.WS_EX_NOACTIVATE     # Don't activate/focus
        )

        # Create window
        self.hwnd = win32gui.CreateWindowEx(
            ex_style,
            self.wc.lpszClassName,
            "GazeTracker Overlay",
            win32con.WS_POPUP,
            0, 0, screen_width, screen_height,
            0, 0, self.wc.hInstance, None
        )

        # Set the window to use alpha for transparency
        win32gui.SetLayeredWindowAttributes(
            self.hwnd,
            0,
            self.window_opacity,
            win32con.LWA_ALPHA
        )

    def _create_brush(self):
        if self.brush:
            win32gui.DeleteObject(self.brush)

        # Create brush for window background color
        self.brush = win32gui.CreateSolidBrush(
            win32api.RGB(*self.window_color)  # Use window_color for background
        )

    def _window_proc(self, hwnd, msg, wparam, lparam):
        """Window procedure for handling window messages"""
        if msg == win32con.WM_PAINT:
            if self.should_show:
                hdc, ps = win32gui.BeginPaint(hwnd)
                rect = win32gui.GetClientRect(hwnd)
                
                # Create DC for double buffering
                memdc = win32gui.CreateCompatibleDC(hdc)
                bitmap = win32gui.CreateCompatibleBitmap(hdc, rect[2], rect[3])
                old_bitmap = win32gui.SelectObject(memdc, bitmap)
                
                # Fill background with red
                if not self.brush:
                    self._create_brush()
                win32gui.FillRect(memdc, rect, self.brush)
                
                # Copy to window
                win32gui.BitBlt(
                    hdc, 0, 0, rect[2], rect[3],
                    memdc, 0, 0, win32con.SRCCOPY
                )
                
                # Cleanup
                win32gui.SelectObject(memdc, old_bitmap)
                win32gui.DeleteObject(bitmap)
                win32gui.DeleteDC(memdc)
                win32gui.EndPaint(hwnd, ps)
                return 0
                
        elif msg == win32con.WM_DESTROY:
            win32gui.PostQuitMessage(0)
            return 0
        
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def _delayed_hide(self):
        """Callback для отложенного скрытия окна"""
        self.should_show = False

    def _run_window(self):
        """Run the overlay window"""
        self._create_overlay_window()
        
        while not self.close_event.is_set():
            if win32gui.PumpWaitingMessages() == -1:  # WM_QUIT received
                break
                
            if self.should_show != self.is_visible:
                if self.should_show:
                    if not win32gui.IsWindowVisible(self.hwnd):
                        win32gui.ShowWindow(self.hwnd, win32con.SW_SHOWNA)  # Show without activating
                        win32gui.InvalidateRect(self.hwnd, None, True)
                        win32gui.UpdateWindow(self.hwnd)
                else:
                    if win32gui.IsWindowVisible(self.hwnd):
                        win32gui.ShowWindow(self.hwnd, win32con.SW_HIDE)
                self.is_visible = self.should_show
            
            time.sleep(0.016)  # ~60 FPS

        if self.hwnd:
            try:
                win32gui.DestroyWindow(self.hwnd)
                self.hwnd = None
            except Exception:
                pass  # Window might already be destroyed
                    
    def show(self, show=True):
        """Show or hide the overlay"""
        if show:
            # Если показываем окно, отменяем любой отложенный таймер скрытия
            if self.hide_timer is not None:
                self.hide_timer.cancel()
                self.hide_timer = None
            
            if not self.should_show:  # Только если окно не показано
                self.should_show = True
                if self.hwnd:
                    win32gui.ShowWindow(self.hwnd, win32con.SW_SHOWNA)
                    win32gui.InvalidateRect(self.hwnd, None, True)
                    win32gui.UpdateWindow(self.hwnd)
        else:
            # Если скрываем окно, запускаем таймер
            if self.should_show and self.hide_timer is None:  # Только если окно показано и таймер не запущен
                self.hide_timer = Timer(self.HIDE_DELAY, self._delayed_hide)
                self.hide_timer.start()

    def close(self):
        """Close the overlay window"""
        if self.is_running:
            if self.hide_timer is not None:
                self.hide_timer.cancel()
                self.hide_timer = None
            self.is_running = False
            self.close_event.set()
            self.thread.join(timeout=1.0)  # Wait for thread to finish

    def update(self):
        print("overaly.update()")

    def get_color_hex(self):
        """Get overlay window color as hex string"""
        r, g, b = self.window_color
        return f"#{r:02x}{g:02x}{b:02x}"
        
    def set_color(self, r, g, b):
        """Set overlay window color"""
        self.window_color = (r, g, b)
        if self.hwnd:
            self._create_brush()
    
    def set_color_hex(self, hex_color):
        """Set overlay window color from hex string"""
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        self.set_color(r, g, b)
        
    def set_opacity(self, opacity):
        """Set overlay window opacity (0-255)"""
        self.window_opacity = max(0, min(255, opacity))
        if self.hwnd:
            # Set the window to use alpha for transparency
            win32gui.SetLayeredWindowAttributes(
                self.hwnd,
                0,
                self.window_opacity,
                win32con.LWA_ALPHA
            )
