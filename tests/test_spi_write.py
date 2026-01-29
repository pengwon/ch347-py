import os
import sys

# Get the parent directory's path
parent_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Add the parent directory to the system path if not already present
if parent_directory not in sys.path:
    sys.path.insert(0, parent_directory)

from ch347 import CH347, SPIConfig

spi_config = SPIConfig(
    Mode=0,
    Clock=2,
    ByteOrder=1,
    SpiWriteReadInterval=0,
    SpiOutDefaultData=0xFF,
    ChipSelect=0x80,
    CS1Polarity=0,
    CS2Polarity=0,
    IsAutoDeative=1,
    ActiveDelay=0,
    DelayDeactive=0,
)

ch347 = CH347()
ch347.open_device()
print(ch347.get_version())
ch347.spi_init(spi_config)
ch347.spi_write(0x80, [0x01])
ch347.close_device()
