"""Load the CH347 command library for the platform ch347-py is running on."""

import ctypes
import ctypes.util
import sys

from ch347.linux_library import LinuxCH347Library

# Windows finds the driver's library in its own directories when no path is given.
WINDOWS_LIBRARY_NAME = "CH347DLLA64"


def load_library(dll_path=None):
    """Return the library object that `CH347` calls into.

    Args:
        dll_path (str, optional): Path to CH347DLLA64.DLL on Windows, or to
            libch347.so on Linux. When None the platform library is searched
            for in the system directories.

    Returns:
        On Windows the loaded DLL, on Linux a `LinuxCH347Library` that presents
        the same functions over WCH's POSIX library.

    Raises:
        OSError: If this platform has no CH347 command library, or the configured
            one cannot be found.
    """
    if sys.platform == "win32":
        return ctypes.WinDLL(dll_path or WINDOWS_LIBRARY_NAME)
    if sys.platform.startswith("linux"):
        return LinuxCH347Library(_load_shared_library(dll_path))
    raise OSError(
        f"ch347-py needs a CH347 command library, and WCH only ships one for Windows "
        f"(CH347DLLA64.DLL) and Linux (libch347.so), not for {sys.platform}. The UART "
        "pins still work as a plain serial port through pyserial."
    )


def _load_shared_library(dll_path):
    path = dll_path or ctypes.util.find_library("ch347") or "libch347.so"
    try:
        return ctypes.CDLL(path)
    except OSError as exc:
        raise OSError(
            f"Could not load the CH347 library {path}: {exc}. WCH ships libch347.so in "
            "https://github.com/WCHSoftGroup/ch341par_linux -- copy "
            "lib/<arch>/dynamic/libch347.so to /usr/lib (and install its ch34x_pis "
            "kernel driver), or pass dll_path=..."
        ) from exc
