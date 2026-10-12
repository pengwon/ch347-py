"""Offline tests for the Linux backend, which needs neither libch347.so nor hardware."""

import ctypes
import sys
from unittest.mock import MagicMock

import pytest

from ch347 import CH347
from ch347.library import load_library
from ch347.linux_library import LinuxCH347Library

DEVICE_FD = 7


class FakeLibrary:
    """Stand-in for libch347.so: records calls, returns True unless told otherwise."""

    def __init__(self, **returns):
        self.calls = []
        self.returns = dict(returns)
        self.side_effects = {}

    def __getattr__(self, function):
        if function.startswith("_"):
            raise AttributeError(function)

        def call(*args):
            self.calls.append((function, args))
            effect = self.side_effects.get(function)
            if effect is not None:
                return effect(*args)
            return self.returns.get(function, True)

        # The prototypes configured by ch347.py are assigned onto these.
        call.argtypes = None
        call.restype = None
        self.__dict__[function] = call
        return call

    def arguments_to(self, function):
        return [args for name, args in self.calls if name == function]


@pytest.fixture
def lib(monkeypatch):
    """A fake libch347.so, loaded as if running on Linux."""
    fake = FakeLibrary(CH347OpenDevice=DEVICE_FD)
    monkeypatch.setattr(ctypes, "CDLL", lambda *args, **kwargs: fake)
    monkeypatch.setattr(sys, "platform", "linux")
    return fake


@pytest.fixture
def device(lib):
    ch347 = CH347()
    assert ch347.open_device() == DEVICE_FD
    assert lib.arguments_to("CH347OpenDevice") == [(b"/dev/ch34x_pis0",)]
    return ch347


def test_load_library_picks_the_posix_library(lib):
    assert isinstance(load_library(), LinuxCH347Library)


def test_load_library_still_uses_the_dll_on_windows(monkeypatch):
    dll = MagicMock()
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(ctypes, "WinDLL", lambda *args: dll)
    assert load_library() is dll


def test_load_library_explains_other_platforms(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    with pytest.raises(OSError, match="libch347.so"):
        load_library()


def test_missing_library_names_what_to_install(monkeypatch):
    def refuse(*args):
        raise OSError("libch347.so: cannot open shared object file")

    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(ctypes, "CDLL", refuse)

    with pytest.raises(OSError, match="ch341par_linux"):
        load_library(dll_path="libch347.so")


def test_device_index_becomes_a_file_descriptor(device, lib):
    io_dir, io_data = [0], [0]

    assert device.gpio_get(io_dir, io_data) is True
    assert device.gpio_set(0x80, 0x80, 0x80) is True
    assert lib.arguments_to("CH347GPIO_Get")[0][0] == DEVICE_FD
    assert lib.arguments_to("CH347GPIO_Set")[0] == (DEVICE_FD, 0x80, 0x80, 0x80)


def test_a_dev_path_may_replace_the_index(lib):
    ch347 = CH347(device_index="/dev/hidraw0")

    assert ch347.open_device() == DEVICE_FD
    assert lib.arguments_to("CH347OpenDevice") == [(b"/dev/hidraw0",)]


def test_failed_open_is_reported_as_no_handle(lib):
    lib.returns["CH347OpenDevice"] = -2

    assert CH347().open_device() is None


def test_close_forgets_the_file_descriptor(device, lib):
    assert device.close_device() is True
    assert lib.arguments_to("CH347CloseDevice") == [(DEVICE_FD,)]

    with pytest.raises(OSError, match="not open"):
        device.gpio_set(0xFF, 0, 0)


def test_spi_calls_add_the_chip_select_flag(device, lib):
    device.spi_write(0x81, [0x01, 0x02])
    device.spi_read(0x81, [0x03], 2)
    device.spi_write_read(0x80, 4, None)
    device.stream_spi4(0x80, 4, None)

    assert lib.arguments_to("CH347SPI_Write")[0][:5] == (DEVICE_FD, False, 0x81, 2, 512)
    assert lib.arguments_to("CH347SPI_Read")[0][:4] == (DEVICE_FD, False, 0x81, 1)
    # CH347StreamSPI4 is the same 4-wire transfer as CH347SPI_WriteRead.
    write_read = lib.arguments_to("CH347SPI_WriteRead")
    assert len(write_read) == 2
    assert write_read[0][1:4] == write_read[1][1:4] == (False, 0x80, 4)


def test_differently_named_posix_functions_are_found(device, lib):
    device.i2c_set_driver_mode(1)
    device.stream_i2c_ret_ack(b"\x68\x00", 1)

    assert lib.arguments_to("CH347I2C_SetDriveMode") == [(DEVICE_FD, 1)]
    assert lib.arguments_to("CH347StreamI2C_RetAck")[0][:2] == (DEVICE_FD, 2)


def test_device_info_reports_what_a_posix_device_knows(device, lib):
    def report_id(fd, pointer):
        ctypes.cast(pointer, ctypes.POINTER(ctypes.c_uint32))[0] = 0x1A86_55DE
        return True

    lib.side_effects["CH34X_GetDeviceID"] = report_id

    info = device.get_device_info()

    assert info.DeviceIndex == 0
    assert info.DevicePath == b"/dev/ch34x_pis0"
    assert info.DevHandle == DEVICE_FD
    assert info.DeviceID == b"USB\\VID_1A86&PID_55DE"


def test_chip_type_is_read_from_the_posix_chip_type_call(device, lib):
    def report_type(fd, pointer):
        ctypes.cast(pointer, ctypes.POINTER(ctypes.c_int))[0] = 2
        return True

    lib.side_effects["CH34x_GetChipType"] = report_type

    assert device.get_chip_type() == 2


def test_interrupt_mode_becomes_a_kernel_irq_type(device, lib):
    received = []

    def read_status(istatus):
        pin_state = ctypes.cast(istatus, ctypes.POINTER(ctypes.c_ubyte * 8)).contents
        received.append(list(pin_state))

    device.set_interrupt(4, 0, 8, 3, read_status)

    fd, pin, enabled, irq_type, handler = lib.arguments_to("CH347GPIO_IRQ_Set")[-1]
    assert (fd, pin, enabled, irq_type) == (DEVICE_FD, 4, True, 2)  # falling edge
    handler(34)  # what the library does when the pin triggers
    assert received == [[0] * 8]


@pytest.mark.parametrize(
    ("windows_mode", "posix_irq_type"),
    [(0, 2), (1, 1), (2, 3)],
    ids=["falling", "rising", "both"],
)
def test_every_trip_mode_is_translated(device, lib, windows_mode, posix_irq_type):
    device.set_interrupt(4, windows_mode, 8, 3, lambda status: None)

    assert lib.arguments_to("CH347GPIO_IRQ_Set")[-1][3] == posix_irq_type


def test_registering_another_pin_releases_the_previous_one(device, lib):
    device.set_interrupt(4, 0, 8, 3, lambda status: None)
    device.set_interrupt(5, 1, 8, 3, lambda status: None)

    disabled = lib.arguments_to("CH347GPIO_IRQ_Set")[1]
    assert disabled[1:4] == (4, False, 0)
    assert lib.arguments_to("CH347GPIO_IRQ_Set")[-1][1:3] == (5, True)


def test_interrupt_is_disabled_without_a_callback(device, lib):
    device.set_interrupt(4, 0, 8, 3, lambda status: None)

    assert device.set_interrupt(0xFF, 3, 0xFF, 3, None) is True
    assert lib.arguments_to("CH347GPIO_IRQ_Set")[-1][1:3] == (4, False)


def test_abort_releases_the_registered_pin(device, lib):
    device.set_interrupt(4, 0, 8, 3, lambda status: None)

    assert device.abort_interrupt() is True
    assert lib.arguments_to("CH347GPIO_IRQ_Set")[-1][1:3] == (4, False)


def test_a_second_interrupt_source_is_refused(device):
    with pytest.raises(NotImplementedError, match="one GPIO interrupt"):
        device.set_interrupt(4, 0, 5, 0, lambda status: None)


@pytest.mark.parametrize(
    ("call", "hint"),
    [
        (lambda d: d.set_device_notify(b"vid_1a86\x00"), "udev monitor"),
        (lambda d: d.get_version(), "CH34x_GetDriverVersion"),
        (lambda d: d.get_serial_number(), "CH34X_GetDeviceID"),
        (lambda d: d.read_data(None, None), "stream transfers"),
        (lambda d: d.spi_set_chip_select(1, 1, 1, 1, 1), "spi_init"),
        (lambda d: d.uart_open(), "/dev/tty*"),
        (lambda d: d.uart_set_notify(b"vid_1a86\x00"), "/dev/tty*"),
    ],
    ids=["notify", "version", "serial", "read", "chipselect", "uart", "uart-notify"],
)
def test_windows_only_calls_point_at_the_posix_alternative(device, call, hint):
    with pytest.raises(NotImplementedError, match=hint):
        call(device)
