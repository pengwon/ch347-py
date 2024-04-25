import sys
import os

# Get the parent directory's path
parent_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

# Add the parent directory to the system path if not already present
if parent_directory not in sys.path:
    sys.path.insert(0, parent_directory)

import ch347

class SDNAND:
    def __init__(self, cs=0, driver=ch347.CH347()):
        spi_config = ch347.SPIConfig(
            Mode = 0,
            Clock = 0,
            ByteOrder = 1,
            SpiWriteReadInterval = 0,
            SpiOutDefaultData = 0,
            ChipSelect = 0x80
            CS1Polarity = 0,
            CS2Polarity = 0,
            IsAutoDeative = 1,
            ActiveDelay = 0,
            DelayDeactive = 0
        )
        self.driver = driver
        self.driver.open_device()
        self.driver.spi_init(spi_config)

    def send_cmd(self, cmd, arg):
        self.driver.spi_write([cmd] + [(arg >> (24 - (8 * i))) & 0xFF for i in range(4)])

    def read_register(self, cmd, length):
        self.send_cmd(cmd, 0)
        return self.driver.spi_read(length)

    def initialize(self):
        self.send_cmd(0, 0)  # CMD0: GO_IDLE_STATE
        self.send_cmd(8, 0x1AA)  # CMD8: SEND_IF_COND
        self.send_cmd(55, 0)  # CMD55: APP_CMD
        self.send_cmd(41, 0x40000000)  # ACMD41: SD_SEND_OP_COND
        while True:
            response = self.read_register(41, 1)
            if response[0] & 0x80:
                break
        self.send_cmd(2, 0)  # CMD2: ALL_SEND_CID
        self.send_cmd(3, 0)  # CMD3: SEND_RELATIVE_ADDR