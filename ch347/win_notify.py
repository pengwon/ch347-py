"""Message pumping for the DLL's device-notification window.

`CH347SetDeviceNotify` creates a hidden window (class CH347PAR_NotifyWnd, seen
with the shipping CH347DLLA64) on the thread that calls it, and the driver
reports plug/unplug through WM_DEVICECHANGE posted to that window. Windows only
dispatches queued messages from a thread that pumps, so a console program that
sleeps never runs the callback. `DeviceNotifyPump` registers on a thread that
pumps, which is what `CH347.start_device_notify` uses.
"""

import ctypes
import ctypes.wintypes as wintypes
import threading

PM_REMOVE = 0x0001

# How long the pump sleeps when the queue is empty; bounds how late a hotplug
# callback can arrive.
IDLE_INTERVAL = 0.01


class DeviceNotifyPump(threading.Thread):
    """Registers the notification, then dispatches messages until stopped."""

    def __init__(self, register, cancel):
        """
        Args:
            register: Called on this thread; returns True when registered.
            cancel: Called on this thread after the last message is dispatched.
        """
        super().__init__(name="ch347-device-notify", daemon=True)
        self._register = register
        self._cancel = cancel
        self._stop_requested = threading.Event()
        self._registration_done = threading.Event()
        self.registered = None
        self.error = None

    def wait_registered(self):
        """Wait for the registration, re-raising whatever it raised."""
        self._registration_done.wait()
        if self.error is not None:
            raise self.error
        return self.registered

    def run(self):
        try:
            self.registered = bool(self._register())
        except BaseException as exc:
            self.error = exc
        finally:
            self._registration_done.set()
        if not self.registered:
            return

        user32 = ctypes.windll.user32
        message = wintypes.MSG()
        while not self._stop_requested.is_set():
            if user32.PeekMessageW(ctypes.byref(message), None, 0, 0, PM_REMOVE):
                user32.TranslateMessage(ctypes.byref(message))
                user32.DispatchMessageW(ctypes.byref(message))
            else:
                self._stop_requested.wait(IDLE_INTERVAL)
        self._cancel()

    def stop(self, timeout=2.0):
        """Ask the pump to quit; returns True once its thread is gone."""
        self._stop_requested.set()
        self.join(timeout)
        return not self.is_alive()
