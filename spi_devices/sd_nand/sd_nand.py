import os
import sys

# Get the parent directory's path
parent_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

# Add the parent directory to the system path if not already present
if parent_directory not in sys.path:
    sys.path.insert(0, parent_directory)

import ch347


class Response:
    def __init__(self, data):
        self.data = data

    def get_raw_data(self):
        return self.data

    def parse(self):
        raise NotImplementedError("Subclasses should implement this!")


class R1Response(Response):
    def parse(self):
        # Parse the data for an R1 response
        pass


class R2Response(Response):
    def parse(self):
        # Parse the data for an R2 response
        pass


class R3Response(Response):
    def parse(self):
        # Parse the data for an R3 response
        pass


class R6Response(Response):
    def parse(self):
        # Parse the data for an R4 response
        pass


class R7Response(Response):
    def parse(self):
        # Parse the data for an R7 response
        pass


class SD_NAND:
    def __init__(self, cs=0, driver=ch347.CH347()):
        spi_config = ch347.SPIConfig(
            Mode=0,
            Clock=2,
            ByteOrder=1,
            SpiWriteReadInterval=0,
            SpiOutDefaultData=0xFF,
            ChipSelect=0x80 if cs == 0 else 0x81,
            CS1Polarity=0,
            CS2Polarity=0,
            IsAutoDeative=1,
            ActiveDelay=0,
            DelayDeactive=0,
        )
        self.driver = driver
        self.driver.open_device()
        self.driver.spi_init(spi_config)

    def _crc7(data):
        crc = 0
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc ^= 0x09
                    crc <<= 1
                else:
                    crc <<= 1
        return (crc >> 1) & 0x7F

    def _send_cmd(self, cmd, arg, is_acmd=False) -> Response:
        if is_acmd:
            self.send_cmd(55, 0)
        chip_select = 0x80  # Replace with the correct value for your application
        data = [cmd] + [(arg >> (24 - (8 * i))) & 0xFF for i in range(4)]
        # SPI模式下仅CMD0命令需要校验CRC，其余命令均忽略, CMD0命令CRC固定为0x95
        # crc = self._crc7(data)
        # data.append((crc << 1) | 0x01)
        data.append(0x95)
        if cmd == 8:
            return R7Response(self.driver.spi_read(chip_select, data, 9))
        elif cmd == 58:
            return R3Response(self.driver.spi_read(chip_select, data, 9))
        elif cmd == 13:
            return R2Response(self.driver.spi_read(chip_select, data, 10))
        else:
            return R1Response(self.driver.spi_read(chip_select, data, 9))

    def initialize(self):
        # self.driver.spi_change_cs(1)
        self.driver.spi_write(0x00, [0xFF] * 10)
        response = self._send_cmd(0, 0)  # CMD0: GO_IDLE_STATE
        print(response.get_raw_data())
        # self.send_cmd(8, 0x1AA)  # CMD8: SEND_IF_COND
        # self.send_cmd(55, 0)  # CMD55: APP_CMD
        # self.send_cmd(41, 0x40000000)  # ACMD41: SD_SEND_OP_COND
        # while True:
        #     response = self.read_register(41, 1)
        #     if response[0] & 0x80:
        #         break
        # self.send_cmd(2, 0)  # CMD2: ALL_SEND_CID
        # self.send_cmd(3, 0)  # CMD3: SEND_RELATIVE_ADDR
