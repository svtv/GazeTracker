"""
Overlay window for displaying visual alerts
"""

# Standard library imports
from threading import Thread, Event, Timer
import time

# Third-party imports
import win32gui
import win32con
import win32api

class WindowState:
    """State of the overlay window"""
    def __init__(self):
        self.should_show = False
        self.is_running = True
        self.is_visible = False  # Flag of current visibility state
        self.hide_timer = None  # Timer for hide delay
        self.HIDE_DELAY = 0.25  # Hide delay in seconds

class WindowHandles:
    """Window handles and resources"""
    def __init__(self):
        self.wc = None
        self.hwnd = None
        self.brush = None

class WindowAppearance:
    """Window appearance settings"""
    def __init__(self):
        self.window_opacity = 64  # Default window opacity
        self.window_color = (255, 0, 0)  # Default color (red)

class OverlayWindow:
    """Overlay window for displaying visual alerts"""
    def __init__(self):
        """Initialize the overlay window"""
        self.state = WindowState()
        self.handles = WindowHandles()
        self.appearance = WindowAppearance()
        self.close_event = Event()

        # Start window thread
        self.thread = Thread(target=self._run_window, daemon=True)
        self.thread.start()
        time.sleep(0.1)  # Wait for window creation

    def _register_window_class(self):
        """Register the overlay window class"""
        # Get module handle
        # pylint: disable=c-extension-no-member
        try:
            hinst = win32api.GetModuleHandle(None)
            if not hinst:
                print("Failed to get module handle")
                return

            # Register window class
            # pylint: disable=c-extension-no-member
            wc = win32gui.WNDCLASS()
            wc.hInstance = hinst
            wc.lpfnWndProc = self._window_proc
            wc.lpszClassName = "GazeTrackerOverlay"
            wc.style = win32con.CS_HREDRAW | win32con.CS_VREDRAW

            atom = win32gui.RegisterClass(wc)
            if atom:
                self.handles.wc = wc

        except win32gui.error as e:
            # Error code 1410: CLASS_ALREADY_EXISTS
            if e.winerror == 1410:
                # Class already registered, which is fine
                pass
            else:
                # Re-raise unexpected win32gui errors
                raise

        except win32api.error as e:
            # Handle GetModuleHandle errors
            print(f"Failed to get module handle: {e}")

    def _create_overlay_window(self):
        """Create a transparent overlay window"""
        if not self.handles.wc:
            self._register_window_class()

        # Get screen dimensions
        # pylint: disable=c-extension-no-member
        screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        # pylint: disable=c-extension-no-member
        screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)

        # Extended window styles for transparency and click-through
        ex_style = (
            win32con.WS_EX_LAYERED |      # For transparency
            win32con.WS_EX_TRANSPARENT |   # Click-through
            win32con.WS_EX_TOPMOST |       # Always on top
            win32con.WS_EX_NOACTIVATE     # Don't activate/focus
        )

        # Create window
        # pylint: disable=c-extension-no-member
        self.handles.hwnd = win32gui.CreateWindowEx(
            ex_style,
            self.handles.wc.lpszClassName,
            None,
            win32con.WS_POPUP,
            0, 0, screen_width, screen_height,
            None,
            None,
            self.handles.wc.hInstance,
            None
        )

        # Set the window to use alpha for transparency
        # pylint: disable=c-extension-no-member
        win32gui.SetLayeredWindowAttributes(
            self.handles.hwnd,
            0,
            self.appearance.window_opacity,
            win32con.LWA_ALPHA
        )

    def _create_brush(self):
        """Create or recreate the window background brush"""
        if self.handles.brush:
            # pylint: disable=c-extension-no-member
            win32gui.DeleteObject(self.handles.brush)

        # Create brush for window background color
        # pylint: disable=c-extension-no-member
        self.handles.brush = win32gui.CreateSolidBrush(
            # pylint: disable=c-extension-no-member
            win32api.RGB(*self.appearance.window_color)  # Use window_color for background
        )

    def _window_proc(self, hwnd, msg, wparam, lparam):
        """Window procedure for handling window messages"""
        if msg == win32con.WM_PAINT:
            if self.state.should_show:
                hdc, ps = win32gui.BeginPaint(hwnd)
                rect = win32gui.GetClientRect(hwnd)

                # Create DC for double buffering
                memdc = win32gui.CreateCompatibleDC(hdc)
                bitmap = win32gui.CreateCompatibleBitmap(hdc, rect[2], rect[3])
                old_bitmap = win32gui.SelectObject(memdc, bitmap)

                # Fill background with color
                if not self.handles.brush:
                    self._create_brush()
                win32gui.FillRect(memdc, rect, self.handles.brush)

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
            # pylint: disable=c-extension-no-member
            win32gui.PostQuitMessage(0)
            return 0

        # pylint: disable=c-extension-no-member
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def _delayed_hide(self):
        """Callback for delayed window hiding"""
        self.state.should_show = False

    def _run_window(self):
        """Run the overlay window"""
        self._create_overlay_window()

        while self.state.is_running and not self.close_event.is_set():
            # pylint: disable=c-extension-no-member
            if win32gui.PumpWaitingMessages() == -1:  # WM_QUIT received
                break

            if self.state.should_show != self.state.is_visible:
                if self.state.should_show:
                    if not win32gui.IsWindowVisible(self.handles.hwnd):
                        win32gui.ShowWindow(self.handles.hwnd, win32con.SW_SHOWNA)  # Show without activating
                        win32gui.InvalidateRect(self.handles.hwnd, None, True)
                        win32gui.UpdateWindow(self.handles.hwnd)
                else:
                    # If hiding the window, start timer
                    # Only if window is shown and timer is not running
                    if self.state.should_show and self.state.hide_timer is None:
                        self.state.hide_timer = Timer(self.state.HIDE_DELAY, self._delayed_hide)
                        self.state.hide_timer.start()

                    # pylint: disable=c-extension-no-member
                    if win32gui.IsWindowVisible(self.handles.hwnd):
                        # pylint: disable=c-extension-no-member
                        win32gui.ShowWindow(self.handles.hwnd, win32con.SW_HIDE)

                self.state.is_visible = self.state.should_show

            time.sleep(0.016)  # ~60 FPS

        if self.handles.hwnd:
            try:
                # pylint: disable=c-extension-no-member
                win32gui.DestroyWindow(self.handles.hwnd)
                self.handles.hwnd = None

            except win32gui.error as e:
                # Error codes:
                # ERROR_INVALID_WINDOW_HANDLE (1400): Invalid window handle
                # ERROR_INVALID_HANDLE (6): The handle is invalid
                # ERROR_ACCESS_DENIED (5): Access is denied
                if e.winerror in (1400, 6, 5):
                    self.handles.hwnd = None  # Window already destroyed or can't be accessed
                else:
                    # Re-raise unexpected win32gui errors
                    raise
        else:
            pass  # Window might already be destroyed

        if self.handles.brush:
            win32gui.DeleteObject(self.handles.brush)
            self.handles.brush = None

    def show(self, show=True):
        """Show or hide the overlay window"""
        if show:
            # If showing the window, cancel any delayed hide timer
            if self.state.hide_timer is not None:
                self.state.hide_timer.cancel()
                self.state.hide_timer = None

            if not self.state.should_show:  # Only if window is not shown
                self.state.should_show = True
                if self.handles.hwnd:
                    # pylint: disable=c-extension-no-member
                    win32gui.ShowWindow(self.handles.hwnd, win32con.SW_SHOWNA)
                    # pylint: disable=c-extension-no-member
                    win32gui.InvalidateRect(self.handles.hwnd, None, True)
                    # pylint: disable=c-extension-no-member
                    win32gui.UpdateWindow(self.handles.hwnd)
        else:
            # If hiding the window, start timer
            # Only if window is shown and timer is not running
            if self.state.should_show and self.state.hide_timer is None:
                self.state.hide_timer = Timer(self.state.HIDE_DELAY, self._delayed_hide)
                self.state.hide_timer.start()

    def close(self):
        """Close the overlay window"""
        if self.state.is_running:
            if self.state.hide_timer is not None:
                self.state.hide_timer.cancel()
                self.state.hide_timer = None
            self.state.is_running = False
            self.close_event.set()
            self.thread.join(timeout=1.0)  # Wait for thread to finish

    def update(self):
        print("overlay.update()")

    def get_color_hex(self):
        """Get overlay window color as hex string"""
        r, g, b = self.appearance.window_color
        return f"#{r:02x}{g:02x}{b:02x}"

    def set_color(self, r, g, b):
        """Set overlay window color"""
        self.appearance.window_color = (r, g, b)
        if self.handles.hwnd:
            self._create_brush()

    def set_color_hex(self, hex_color):
        """Set overlay window color from hex string"""
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        self.set_color(r, g, b)

    def set_opacity(self, opacity):
        """Set overlay window opacity (0-255)"""
        self.appearance.window_opacity = max(0, min(255, opacity))
        if self.handles.hwnd:
            # Set the window to use alpha for transparency
            # pylint: disable=c-extension-no-member
            win32gui.SetLayeredWindowAttributes(
                self.handles.hwnd,
                0,
                self.appearance.window_opacity,
                win32con.LWA_ALPHA
            )
