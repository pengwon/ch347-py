"""Callback plumbing regression tests for https://github.com/pengwon/ch347-py/issues/5

They run against a stand-in for CH347DLLA64, so no CH347 hardware is needed.
"""

import ctypes
import gc

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
