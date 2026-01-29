# connect GPIO PIN 4 and PIN 7 for testing interrupt callback

import ctypes
import msvcrt  # Windows only, for keyboard input
import os
import random
import string
import sys
import threading
import time


def send_random_uart(ch347, chip_select=0, length=16):
    rand_str = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(length))
    data = rand_str.encode("utf-8")
    length_list = [len(data)]
    result = ch347.uart_write(data, length_list)
    print(f"[Sender] Sent ({length_list[0]} bytes): {rand_str} ")
    return result


def uart_reader(ch347, stop_event, read_size=64):
    while not stop_event.is_set():
        read_len = [read_size]
        buffer = (ctypes.c_char * read_size)()
        result = ch347.uart_read(buffer, read_len)
        if result and read_len[0] > 0:
            data = bytes(buffer[: read_len[0]]).decode("utf-8", errors="ignore")
            print(f"[Reader] Recv ({read_len[0]}) bytes: {data}")
        time.sleep(0.1)


def uart_writer(ch347, stop_event, length=16):
    while not stop_event.is_set():
        send_random_uart(ch347, length)
        time.sleep(1)


def uart_loop_multithread(ch347):
    stop_event = threading.Event()

    reader_thread = threading.Thread(target=uart_reader, args=(ch347, stop_event))
    writer_thread = threading.Thread(target=uart_writer, args=(ch347, stop_event))

    reader_thread.start()
    writer_thread.start()

    print("Sending every 1s, reading every 0.1s. Press 'x' to stop.")
    while True:
        if msvcrt.kbhit():
            if msvcrt.getwch().lower() == "x":
                print("Exit requested.")
                stop_event.set()
                break
        time.sleep(0.05)

    reader_thread.join()
    writer_thread.join()
    print("Program terminated.")


# Get the parent directory's path
parent_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Add the parent directory to the system path if not already present
if parent_directory not in sys.path:
    sys.path.insert(0, parent_directory)

from ch347 import CH347

ch347 = CH347()

print("version:", ch347.get_version())

status = ch347.uart_open()
print("uart_open", status)

status = ch347.uart_init(115200, 8, 0, 1, 5000)
print("uart_init", status)

# Get device information
device_info = ch347.uart_get_device_info()
print("uart_get_device_info", device_info)


status = ch347.uart_set_timeout(500, 500)
print("uart_set_timeout", status)

uart_loop_multithread(ch347)

status = ch347.uart_close()
print("uart_close", status)
