"""Callback plumbing regression tests for https://github.com/pengwon/ch347-py/issues/5

They run against a stand-in for CH347DLLA64, so no CH347 hardware is needed.
"""

import ctypes
import gc
import sys
import threading

import pytest

from ch347 import CH347

pytestmark = pytest.mark.skipif(
    not hasattr(ctypes, "WinDLL"), reason="the Windows library is loaded through ctypes.WinDLL"
)


class RecordedFunction:
    def __init__(self):
        self.calls = []

    def __call__(self, *args):
        self.calls.append(args)
        return True


class FakeDll:
    """Minimal stand-in for the CH347 DLL: records prototype setup and calls."""

    def __init__(self):
        self._functions = {}

    def __getattr__(self, name):
        # Only reached for names not found normally, so `argtypes`/`restype`
        # assignments by CH347.__init__ land on the recorded function object.
        function = self._functions.setdefault(name, RecordedFunction())
        return function

    def calls_to(self, name):
        return self._functions[name].calls

    def prototype(self, name):
        return self._functions[name].argtypes


@pytest.fixture
def dll(monkeypatch):
    fake = FakeDll()
    monkeypatch.setattr(ctypes, "WinDLL", lambda *args, **kwargs: fake)
    return fake


def test_registered_callback_survives_the_call(dll):
    events = []
    device = CH347()

    assert device.set_device_notify(b"vid_1a86\x00", events.append) is True
    ((index, device_id, callback),) = dll.calls_to("CH347SetDeviceNotify")
    assert (index, device_id) == (0, b"vid_1a86\x00")

    # Without a live reference the DLL would call through a dangling pointer.
    gc.collect()
    assert callback is device.callback_func
    callback(CH347.DEVICE_ARRIVAL)
    assert events == [CH347.DEVICE_ARRIVAL]


def test_default_notify_callback_matches_the_dll_signature(dll, capsys):
    device = CH347()
    device.set_device_notify("vid_1a86")

    ((callback),) = [args[-1] for args in dll.calls_to("CH347SetDeviceNotify")]
    callback(CH347.DEVICE_ARRIVAL)
    callback(CH347.DEVICE_REMOVE)

    captured = capsys.readouterr()
    assert "Device inserted" in captured.out
    assert "Device unplugged" in captured.out
    assert "Exception ignored" not in captured.err


def test_none_cancels_the_notification(dll):
    device = CH347()
    device.set_device_notify(b"vid_1a86\x00", None)

    ((callback),) = [args[-1] for args in dll.calls_to("CH347SetDeviceNotify")]
    assert not callback


@pytest.mark.parametrize(
    ("function", "register"),
    [
        ("CH347SetDeviceNotify", lambda d: d.set_device_notify(b"vid_1a86\x00")),
        ("CH347Uart_SetDeviceNotify", lambda d: d.uart_set_notify(b"vid_1a86\x00")),
    ],
    ids=["device", "uart"],
)
def test_the_device_id_is_handed_over_as_a_byte_string(dll, function, register):
    """CH347DLL_EN.H declares PCHAR; POINTER(c_ubyte) would reject the bytes."""
    device = CH347()

    register(device)

    assert dll.prototype(function)[1] is ctypes.c_char_p
    assert dll.calls_to(function)[-1][1] == b"vid_1a86\x00"


def test_default_interrupt_callback_matches_the_dll_signature(dll, capsys):
    device = CH347()
    status = (ctypes.c_ubyte * 8)(0x00, 0x20, 0x28, 0x00, 0x00, 0x00, 0x00, 0x00)

    assert device.set_interrupt(1, 0, 2, 0) is True
    ((callback),) = [args[-1] for args in dll.calls_to("CH347SetIntRoutine")]
    callback(status)

    captured = capsys.readouterr()
    assert "0x00 0x20 0x28" in captured.out
    assert "Exception ignored" not in captured.err


def test_interrupt_can_be_disabled(dll):
    device = CH347()

    device.set_interrupt(0xFF, 3, 0xFF, 3, None)

    ((callback),) = [args[-1] for args in dll.calls_to("CH347SetIntRoutine")]
    assert not callback


def test_notification_registers_on_a_pumping_thread(dll):
    device = CH347()
    registered_on = []

    record = dll.CH347SetDeviceNotify

    def record_thread(index, device_id, callback):
        registered_on.append(threading.get_ident())
        return record(index, device_id, callback)

    dll.CH347SetDeviceNotify = record_thread
    try:
        assert device.start_device_notify(b"vid_1a86\x00", lambda status: None) is True
        assert device._notify_pump.is_alive()
        assert registered_on[0] == device._notify_pump.ident
        assert registered_on[0] != threading.get_ident()
    finally:
        assert device.stop_device_notify() is True

    # Stopping cancels the notification, from the thread that owns the window.
    ((index, device_id, callback),) = dll.calls_to("CH347SetDeviceNotify")[1:]
    assert device_id == b"vid_1a86\x00"
    assert not callback
    assert registered_on[-1] == registered_on[0]


def test_starting_notification_twice_replaces_the_previous_pump(dll):
    device = CH347()
    device.start_device_notify(b"vid_1a86\x00", lambda status: None)
    first = device._notify_pump

    device.start_device_notify(b"vid_1a86\x00", lambda status: None)

    assert not first.is_alive()
    assert device.stop_device_notify() is True
    assert device.stop_device_notify() is False


def test_notification_is_windows_only(dll, monkeypatch):
    device = CH347()
    monkeypatch.setattr(sys, "platform", "linux")

    with pytest.raises(OSError, match="udev"):
        device.start_device_notify(b"vid_1a86\x00")


def test_pump_cancels_when_stopped():
    from ch347.win_notify import DeviceNotifyPump

    calls = []
    pump = DeviceNotifyPump(
        lambda: calls.append("register") or True, lambda: calls.append("cancel")
    )
    pump.start()

    assert pump.wait_registered() is True
    assert calls == ["register"]
    assert pump.stop() is True
    assert calls == ["register", "cancel"]


def test_pump_exits_when_registration_fails():
    from ch347.win_notify import DeviceNotifyPump

    pump = DeviceNotifyPump(lambda: False, lambda: None)
    pump.start()

    assert pump.wait_registered() is False
    assert pump.stop() is True


def test_pump_reports_registration_errors():
    from ch347.win_notify import DeviceNotifyPump

    def refuse():
        raise ctypes.ArgumentError("no notification window")

    pump = DeviceNotifyPump(refuse, lambda: None)
    pump.start()
    try:
        with pytest.raises(ctypes.ArgumentError):
            pump.wait_registered()
    finally:
        pump.join()
