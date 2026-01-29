import os
import sys

# Get the parent directory's path
parent_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Add the parent directory to the system path if not already present
if parent_directory not in sys.path:
    sys.path.insert(0, parent_directory)

from spi_devices.sd_nand import SD_NAND

sd_nand = SD_NAND()
sd_nand.initialize()
