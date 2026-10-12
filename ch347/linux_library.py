"""WCH's POSIX CH347 library, behind the call surface of CH347DLLA64.DLL.

`CH347` talks to its library the way the Windows driver expects it: every call
takes a device *index* as its first argument, the SPI transfers carry no
chip-select control flag, and ctypes prototypes get declared by assigning
`argtypes`/`restype` onto the library object. `libch347.so` -- the library WCH
ships with the `ch34x_pis` kernel driver in
https://github.com/WCHSoftGroup/ch341par_linux -- differs in each of those
ways, so the translation lives here instead of inside `CH347`.

Functions without a POSIX counterpart raise `NotImplementedError` naming what to
use instead.
"""

import ctypes
import os

# Device nodes created by the ch34x_pis kernel driver, one per interface.
DEVICE_PATH_TEMPLATE = "/dev/ch34x_pis{}"

# CH347.open_device reports a failed open this way, whichever library it loaded.
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

# CH347SetIntRoutine numbers its trip modes (0=falling, 1=rising, 2=both)
# differently from the IRQ_TYPE_EDGE_* values CH347GPIO_IRQ_Set expects.
TRIP_MODE_TO_IRQ_TYPE = {0: 2, 1: 1, 2: 3}

# One status byte per GPIO pin, as mPCH347_INT_ROUTINE documents.
GPIO_STATUS_BYTES = 8

# void handler(int signo): how the POSIX library delivers an edge interrupt.
SIGNAL_ROUTINE = ctypes.CFUNCTYPE(None, ctypes.c_int)

UART_HINT = "in its UART modes the chip's serial port shows up as /dev/tty*, which pyserial drives"


class _EntryPoint:
    """One Windows-named function of the POSIX library.

    `CH347.__init__` configures ctypes prototypes by assigning onto every
    function of the library it loaded. These entry points already carry
    prototypes for libch347.so, so the assignments only have to be tolerated --
    which an ordinary object does, while a bound method rejects attributes.
    """

    def __init__(self, implementation):
        self._implementation = implementation

    def __call__(self, *args):
        return self._implementation(*args)


def _missing_on_posix(function, replacement):
    """Implementation for the Windows calls libch347.so has no counterpart for."""

    def report(*args):
        raise NotImplementedError(f"{function} has no POSIX equivalent: {replacement}")

    return report


def _is_null(pointer):
    """ctypes callback objects hide their address, so cast it to read it."""
    return ctypes.cast(pointer, ctypes.c_void_p).value is None


def _configure_prototypes(lib):
    """Declare libch347.so's own prototypes; the Windows ones would be wrong.

    Output parameters that `CH347` allocates -- the transfer length and the ACK
    count -- are declared as `c_void_p`: the caller's own objects are `c_ulong`,
    which is eight bytes on LP64 and would not convert to a pointer of four.
    """
    boolean = ctypes.c_bool
    byte = ctypes.c_ubyte
    fd = ctypes.c_int

    lib.CH347OpenDevice.argtypes = [ctypes.c_char_p]
    lib.CH347OpenDevice.restype = fd
    lib.CH347CloseDevice.argtypes = [fd]
    lib.CH347CloseDevice.restype = boolean
    lib.CH34xSetTimeout.argtypes = [fd, ctypes.c_uint32, ctypes.c_uint32]
    lib.CH34xSetTimeout.restype = boolean
    lib.CH34X_GetDeviceID.argtypes = [fd, ctypes.POINTER(ctypes.c_uint32)]
    lib.CH34X_GetDeviceID.restype = boolean
    lib.CH34x_GetChipType.argtypes = [fd, ctypes.POINTER(ctypes.c_int)]
    lib.CH34x_GetChipType.restype = boolean
    lib.CH347GPIO_Get.argtypes = [fd, ctypes.POINTER(byte), ctypes.POINTER(byte)]
    lib.CH347GPIO_Get.restype = boolean
    lib.CH347GPIO_Set.argtypes = [fd, byte, byte, byte]
    lib.CH347GPIO_Set.restype = boolean
    lib.CH347GPIO_IRQ_Set.argtypes = [fd, byte, boolean, byte, SIGNAL_ROUTINE]
    lib.CH347GPIO_IRQ_Set.restype = boolean
    lib.CH347SPI_Init.argtypes = [fd, ctypes.c_void_p]
    lib.CH347SPI_Init.restype = boolean
    lib.CH347SPI_GetCfg.argtypes = [fd, ctypes.c_void_p]
    lib.CH347SPI_GetCfg.restype = boolean
    lib.CH347SPI_ChangeCS.argtypes = [fd, byte]
    lib.CH347SPI_ChangeCS.restype = boolean
    lib.CH347SPI_SetFrequency.argtypes = [fd, ctypes.c_uint32]
    lib.CH347SPI_SetFrequency.restype = boolean
    lib.CH347SPI_SetDataBits.argtypes = [fd, byte]
    lib.CH347SPI_SetDataBits.restype = boolean
    lib.CH347SPI_Write.argtypes = [fd, boolean, byte, ctypes.c_int, ctypes.c_int, ctypes.c_void_p]
    lib.CH347SPI_Write.restype = boolean
    lib.CH347SPI_Read.argtypes = [
        fd,
        boolean,
        byte,
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.c_void_p,
    ]
    lib.CH347SPI_Read.restype = boolean
    lib.CH347SPI_WriteRead.argtypes = [fd, boolean, byte, ctypes.c_int, ctypes.c_void_p]
    lib.CH347SPI_WriteRead.restype = boolean
    lib.CH347I2C_Set.argtypes = [fd, ctypes.c_int]
    lib.CH347I2C_Set.restype = boolean
    lib.CH347I2C_SetDelaymS.argtypes = [fd, ctypes.c_int]
    lib.CH347I2C_SetDelaymS.restype = boolean
    lib.CH347I2C_SetStretch.argtypes = [fd, boolean]
    lib.CH347I2C_SetStretch.restype = boolean
    lib.CH347I2C_SetDriveMode.argtypes = [fd, byte]
    lib.CH347I2C_SetDriveMode.restype = boolean
    lib.CH347StreamI2C.argtypes = [fd, ctypes.c_int, ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
    lib.CH347StreamI2C.restype = boolean
    lib.CH347StreamI2C_RetAck.argtypes = [
        fd,
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.c_void_p,
    ]
    lib.CH347StreamI2C_RetAck.restype = boolean
    lib.CH347ReadEEPROM.argtypes = [
        fd,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(byte),
    ]
    lib.CH347ReadEEPROM.restype = boolean
    lib.CH347WriteEEPROM.argtypes = lib.CH347ReadEEPROM.argtypes
    lib.CH347WriteEEPROM.restype = boolean


class LinuxCH347Library:
    """`libch347.so` presenting the function names and arguments of CH347DLLA64."""

    def __init__(self, lib):
        """
        Args:
            lib: The loaded libch347.so, as returned by :func:`ctypes.CDLL`.
        """
        self._lib = lib
        # Windows addresses the device by index on every call, while POSIX calls
        # need the file descriptor CH347OpenDevice handed back for that index.
        self._fds = {}
        # index -> (pin, handler, status buffer) of the registered edge interrupt.
        self._interrupts = {}
        _configure_prototypes(lib)

        for function, implementation in (
            ("CH347OpenDevice", self._open_device),
            ("CH347CloseDevice", self._close_device),
            ("CH347GetDeviceInfor", self._get_device_infor),
            ("CH347GetChipType", self._get_chip_type),
            ("CH347SetIntRoutine", self._set_int_routine),
            ("CH347AbortInter", self._abort_interrupt),
            ("CH347SetTimeout", lambda index, w, r: lib.CH34xSetTimeout(self._fd(index), w, r)),
            ("CH347GPIO_Get", lambda i, d, data: lib.CH347GPIO_Get(self._fd(i), d, data)),
            ("CH347GPIO_Set", lambda i, e, d, data: lib.CH347GPIO_Set(self._fd(i), e, d, data)),
            ("CH347SPI_Init", lambda index, cfg: lib.CH347SPI_Init(self._fd(index), cfg)),
            ("CH347SPI_GetCfg", lambda index, cfg: lib.CH347SPI_GetCfg(self._fd(index), cfg)),
            (
                "CH347SPI_ChangeCS",
                lambda index, status: lib.CH347SPI_ChangeCS(self._fd(index), status),
            ),
            (
                "CH347SPI_SetFrequency",
                lambda index, hz: lib.CH347SPI_SetFrequency(self._fd(index), hz),
            ),
            (
                "CH347SPI_SetDataBits",
                lambda index, bits: lib.CH347SPI_SetDataBits(self._fd(index), bits),
            ),
            (
                "CH347SPI_Write",
                lambda i, cs, length, step, buf: lib.CH347SPI_Write(
                    self._fd(i), False, cs, length, step, buf
                ),
            ),
            (
                "CH347SPI_Read",
                lambda i, cs, w_len, r_len, buf: lib.CH347SPI_Read(
                    self._fd(i), False, cs, w_len, r_len, buf
                ),
            ),
            (
                "CH347SPI_WriteRead",
                lambda i, cs, length, buf: lib.CH347SPI_WriteRead(
                    self._fd(i), False, cs, length, buf
                ),
            ),
            # CH347StreamSPI4 takes the same arguments as CH347SPI_WriteRead.
            (
                "CH347StreamSPI4",
                lambda i, cs, length, buf: lib.CH347SPI_WriteRead(
                    self._fd(i), False, cs, length, buf
                ),
            ),
            ("CH347I2C_Set", lambda index, mode: lib.CH347I2C_Set(self._fd(index), mode)),
            (
                "CH347I2C_SetDelaymS",
                lambda index, delay: lib.CH347I2C_SetDelaymS(self._fd(index), delay),
            ),
            (
                "CH347I2C_SetStretch",
                lambda index, enable: lib.CH347I2C_SetStretch(self._fd(index), enable),
            ),
            (
                "CH347I2C_SetDriverMode",
                lambda index, mode: lib.CH347I2C_SetDriveMode(self._fd(index), mode),
            ),
            (
                "CH347StreamI2C",
                lambda i, w_len, w_buf, r_len, r_buf: lib.CH347StreamI2C(
                    self._fd(i), w_len, w_buf, r_len, r_buf
                ),
            ),
            (
                "CH347StreamI2C_RetACK",
                lambda i, w_len, w_buf, r_len, r_buf, ack: lib.CH347StreamI2C_RetAck(
                    self._fd(i), w_len, w_buf, r_len, r_buf, ack
                ),
            ),
            (
                "CH347ReadEEPROM",
                lambda i, eeprom_id, addr, length, buf: lib.CH347ReadEEPROM(
                    self._fd(i), eeprom_id, addr, length, buf
                ),
            ),
            (
                "CH347WriteEEPROM",
                lambda i, eeprom_id, addr, length, buf: lib.CH347WriteEEPROM(
                    self._fd(i), eeprom_id, addr, length, buf
                ),
            ),
            (
                "CH347SetDeviceNotify",
                _missing_on_posix(
                    "CH347SetDeviceNotify",
                    "watch /dev/ch34x_pis* appear and disappear with a udev monitor instead",
                ),
            ),
            (
                "CH347GetVersion",
                _missing_on_posix(
                    "CH347GetVersion",
                    "the driver version is a string (CH34x_GetDriverVersion), there is no "
                    "library version, and get_chip_type covers the chip",
                ),
            ),
            (
                "CH347GetSerialNumber",
                _missing_on_posix(
                    "CH347GetSerialNumber", "CH34X_GetDeviceID reports the VID and PID only"
                ),
            ),
            (
                "CH347ReadData",
                _missing_on_posix("CH347ReadData", "use the SPI and I2C stream transfers"),
            ),
            (
                "CH347WriteData",
                _missing_on_posix("CH347WriteData", "use the SPI and I2C stream transfers"),
            ),
            (
                "CH347SPI_SetChipSelect",
                _missing_on_posix(
                    "CH347SPI_SetChipSelect",
                    "chip select is configured through the SPIConfig passed to spi_init",
                ),
            ),
            (
                "CH347ReadInter",
                _missing_on_posix(
                    "CH347ReadInter", "POSIX edge interrupts are delivered without a status block"
                ),
            ),
        ):
            self.__dict__[function] = _EntryPoint(implementation)

        for function in (
            "CH347Uart_Open",
            "CH347Uart_Close",
            "CH347Uart_SetDeviceNotify",
            "CH347Uart_GetCfg",
            "CH347Uart_Init",
            "CH347Uart_SetTimeout",
            "CH347Uart_Read",
            "CH347Uart_Write",
            "CH347Uart_QueryBufUpload",
            "CH347Uart_GetDeviceInfor",
        ):
            self.__dict__[function] = _EntryPoint(_missing_on_posix(function, UART_HINT))

    def _pathname(self, index):
        """Device node for an index; a /dev path may be given instead of an index."""
        if isinstance(index, str):
            return index
        return DEVICE_PATH_TEMPLATE.format(index)

    def _fd(self, index):
        try:
            return self._fds[index]
        except KeyError:
            raise OSError(
                f"Device {self._pathname(index)} is not open; call CH347.open_device() first"
            ) from None

    def _open_device(self, index):
        fd = self._lib.CH347OpenDevice(os.fsencode(self._pathname(index)))
        if fd < 0:
            return INVALID_HANDLE_VALUE
        self._fds[index] = fd
        return fd

    def _close_device(self, index):
        fd = self._fds.pop(index, None)
        if fd is None:
            return False
        self._interrupts.pop(index, None)
        return self._lib.CH347CloseDevice(fd)

    def _get_device_infor(self, index, dev_info):
        """Fill the Windows `DeviceInfo` with what a POSIX device can report.

        libch347.so has no CH347GetDeviceInfor, so the fields only the Windows
        driver knows -- endpoint sizes, USB speed, interface number, function
        type -- are left zeroed.
        """
        from ch347.ch347 import DeviceInfo  # imported late: ch347.py imports this module

        fd = self._fd(index)
        info = ctypes.cast(dev_info, ctypes.POINTER(DeviceInfo)).contents
        info.DeviceIndex = index if isinstance(index, int) else 0
        info.DevicePath = os.fsencode(self._pathname(index))
        info.DevHandle = fd
        device_id = ctypes.c_uint32()
        if self._lib.CH34X_GetDeviceID(fd, ctypes.byref(device_id)):
            vid, pid = device_id.value >> 16, device_id.value & 0xFFFF
            info.DeviceID = f"USB\\VID_{vid:04X}&PID_{pid:04X}".encode()
        return True

    def _get_chip_type(self, index):
        chip_type = ctypes.c_int()
        if not self._lib.CH34x_GetChipType(self._fd(index), ctypes.byref(chip_type)):
            return None
        return chip_type.value

    def _set_int_routine(self, index, int0_pin, int0_mode, int1_pin, int1_mode, routine):
        """CH347SetIntRoutine on top of CH347GPIO_IRQ_Set.

        The POSIX library registers one pin per call and delivers the edge as a
        signal, without the 8-byte pin status block the Windows driver hands to
        mPCH347_INT_ROUTINE. The callback is given an all-zero buffer to keep that
        signature; read the pins with `gpio_get` when their levels are needed.
        """
        if int1_pin < 8:
            raise NotImplementedError(
                "CH347SetIntRoutine: libch347.so registers one GPIO interrupt per device, "
                "so there is no second interrupt source to enable"
            )
        fd = self._fd(index)
        self._disable_interrupt(index, fd)
        if _is_null(routine) or int0_pin >= 8:
            # Either the callback was cancelled or no pin was selected, both of
            # which are how the Windows API expresses "no interrupt".
            return True
        try:
            irq_type = TRIP_MODE_TO_IRQ_TYPE[int0_mode]
        except KeyError:
            raise ValueError(f"unknown interrupt mode {int0_mode}") from None

        status = (ctypes.c_ubyte * GPIO_STATUS_BYTES)()
        handler = SIGNAL_ROUTINE(lambda signo: routine(status))
        # Only the pointer reaches the library, so the handler and the buffer it
        # closes over have to stay referenced here.
        self._interrupts[index] = (int0_pin, handler, status)
        return self._lib.CH347GPIO_IRQ_Set(fd, int0_pin, True, irq_type, handler)

    def _disable_interrupt(self, index, fd):
        registered = self._interrupts.pop(index, None)
        if registered is None:
            return False
        pin, _, _ = registered
        return self._lib.CH347GPIO_IRQ_Set(fd, pin, False, 0, None)

    def _abort_interrupt(self, index):
        fd = self._fds.get(index)
        if fd is None:
            return False
        return self._disable_interrupt(index, fd)
