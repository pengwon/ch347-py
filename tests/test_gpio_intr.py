# connect GPIO PIN 4 and PIN 7 for testing interrupt callback

import ctypes
import os
import sys

# Get the parent directory's path
parent_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Add the parent directory to the system path if not already present
if parent_directory not in sys.path:
    sys.path.insert(0, parent_directory)

from ch347 import CH347

# Callback must match: void callback(unsigned char* pdata)
CALLBACK_TYPE = ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.c_ubyte))


@CALLBACK_TYPE
def my_interrupt_callback(pdata):
    # Cast to pointer to array of 8 unsigned bytes
    byte_array = ctypes.cast(pdata, ctypes.POINTER(ctypes.c_ubyte * 8)).contents
    print("Interrupt received:", " ".join(f"0x{b:02X}" for b in byte_array))


ch347 = CH347()
ch347.open_device()

print("open")
print("version:", ch347.get_version())
io_dir = [0]
io_data = [0]

ch347.gpio_get(io_dir, io_data)
print("get_io:", hex(io_dir[0]), hex(io_data[0]))

ch347.gpio_set(0x80, 0x80, 0x00)
ch347.gpio_get(io_dir, io_data)

ch347.set_interrupt(4, 2, 8, 3, my_interrupt_callback)

ch347.gpio_set(0x80, 0x80, 0x80)
ch347.gpio_get(io_dir, io_data)
print("get_io:", hex(io_dir[0]), hex(io_data[0]))

ch347.gpio_set(0x80, 0x80, 0x00)
ch347.gpio_get(io_dir, io_data)
print("get_io:", hex(io_dir[0]), hex(io_data[0]))

ch347.abort_interrupt()

ch347.close_device()
print("close")
