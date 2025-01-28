import win32con
import win32gui

# pylint: disable=c-extension-no-member
def is_screen_on():
    """
    Checks if the screen is on and the system is not locked.

    Returns:
        bool: True if screen is on and system is not locked, False otherwise
    """
    try:
        # Check desktop lock state
        h_desktop = win32gui.OpenDesktop("Default", 0, False, win32con.MAXIMUM_ALLOWED)
        if h_desktop:
            is_locked = not win32gui.SwitchDesktop(h_desktop)
            win32gui.CloseDesktop(h_desktop)
            if is_locked:
                return False

        # Check screen state via WinAPI
        SC_MONITORPOWER = 0xF170
        screen_state = win32gui.SendMessage(win32gui.GetForegroundWindow(),
                                           win32con.WM_SYSCOMMAND,
                                           SC_MONITORPOWER, -1)

        # If screen is in power saving mode or turned off
        if screen_state in [1, 2]:  # 1 - low power mode, 2 - turned off
            return False

        return True
    except Exception:
        return True  # In case of error, assume screen is on
# pylint: enable=c-extension-no-member
