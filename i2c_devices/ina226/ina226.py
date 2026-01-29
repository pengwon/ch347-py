import os
import sys

# Get the parent directory's path
parent_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

# Add the parent directory to the system path if not already present
if parent_directory not in sys.path:
    sys.path.insert(0, parent_directory)

import ch347


class INA226:
    """
    INA226 Sensor Driver.

    This class provides methods for interacting with the INA226 sensor
    using the CH347 I2C driver.

    Attributes:
        CONFIG_REG (int): Address of the configuration register.
        SHUNT_VOLTAGE_REG (int): Address of the shunt voltage register.
        BUS_VOLTAGE_REG (int): Address of the bus voltage register.
        POWER_REG (int): Address of the power register.
        CURRENT_REG (int): Address of the current register.
        CALIBRATION_REG (int): Address of the calibration register.
        MASK_ENABLE_REG (int): Address of the mask/enable register.
        ALERT_LIMIT_REG (int): Address of the alert limit register.
        MANUFACTURER_ID_REG (int): Address of the manufacturer ID register.
        DIE_ID_REG (int): Address of the die ID register.
    """

    CONFIG_REG = 0x00
    SHUNT_VOLTAGE_REG = 0x01
    BUS_VOLTAGE_REG = 0x02
    POWER_REG = 0x03
    CURRENT_REG = 0x04
    CALIBRATION_REG = 0x05
    MASK_ENABLE_REG = 0x06
    ALERT_LIMIT_REG = 0x07
    MANUFACTURER_ID_REG = 0xFE
    DIE_ID_REG = 0xFF

    def __init__(self, address=0x40, r_shunt=20, driver=ch347.CH347()):
        """
        Initialize the INA226 driver.

        Args:
            address (int): I2C address of the INA226 sensor (default is 0x40).
            r_shunt (int): Value of the shunt resistor in milliohm (mΩ) (default is 100).
            driver: An instance of the CH347 driver (default is a new instance).
        """
        self.address = address << 1
        self.r_shunt = r_shunt
        self.driver = driver
        self.driver.open_device()
        self.set_calibration(2048)

    def i2c_read_word(self, register):
        """
        Read a 16-bit word from the specified register via I2C.

        Args:
            register (int): Register address to read from.

        Returns:
            int: The read 16-bit word value.
        """
        raw_data = self.driver.stream_i2c([self.address, register], 2)
        value = (raw_data[0] << 8) | raw_data[1]
        return value

    def i2c_write_word(self, register, value):
        """
        Write a 16-bit word to the specified register via I2C.

        Args:
            register (int): Register address to write to.
            value (int): 16-bit value to write.

        Returns:
            int: Result code (0 for success, -1 for failure).
        """
        if not (0 <= value <= 65535):
            raise ValueError("Value out of range")

        byte1 = value >> 8
        byte2 = value & 0xFF
        return self.driver.stream_i2c([self.address, register, byte1, byte2], 0)

    def reset(self):
        return self.i2c_write_word(self.CONFIG_REG, 0x8000)

    def get_config(self):
        """
        Get the current configuration of the INA226 sensor.

        The Configuration Register settings control the operating modes for the device. This register controls the
        conversion time settings for both the shunt and bus voltage measurements as well as the averaging mode used.
        The operating mode that controls what signals are selected to be measured is also programmed in the
        Configuration Register .

        The Configuration Register can be read from at any time without impacting or affecting the device settings or a
        conversion in progress. Writing to the Configuration Register halts any conversion in progress until the write
        sequence is completed resulting in a new conversion starting based on the new contents of the Configuration
        Register (00h). This halt prevents any uncertainty in the conditions used for the next completed conversion.

        Returns:
            dict: A dictionary with the following keys:

            - "reset" (bool): Reset Bit. True if the reset bit (Bit 15) is set to '1'. Generates a system reset that is
            the same as power-on reset. Resets all registers to default values; this bit self-clears.

            - "avg" (int): Averaging Mode. Bits 9-11 determine the number of samples that are collected and averaged.
            Combinations:
                0: 1    (default)
                1: 4
                2: 16
                3: 64
                4: 128
                5: 256
                6: 512
                7: 1024

            - "vbus_ct" (int): Bus Voltage Conversion Time. Bits 6-8 set the conversion time for the bus voltage measurement.
            Combinations:
                0: 140 µs
                1: 204 µs
                2: 332 µs
                3: 588 µs
                4: 1.1 ms   (default)
                5: 2.116 ms
                6: 4.156 ms
                7: 8.244 ms

            - "vsh_ct" (int): Shunt Voltage Conversion Time. Bits 3-5 set the conversion time for the shunt voltage measurement.
            Combinations:
                0: 140 µs
                1: 204 µs
                2: 332 µs
                3: 588 µs
                4: 1.1 ms   (default)
                5: 2.116 ms
                6: 4.156 ms
                7: 8.244 ms

            - "mode" (int): Operating Mode. Bits 0-2 select continuous, triggered, or power-down mode of operation. These bits default to continuous shunt and bus measurement mode.
            Combinations:
                0: Power-Down (or Shutdown)
                1: Shunt Voltage, Triggered
                2: Bus Voltage, Triggered
                3: Shunt and Bus, Triggered
                4: Power-Down (or Shutdown)
                5: Shunt Voltage, Continuous
                6: Bus Voltage, Continuous
                7: Shunt and Bus, Continuous    (default)
        """
        # Read the current value of CONFIG_REG
        config_value = self.i2c_read_word(self.CONFIG_REG)

        # Parse the configuration settings
        config = {
            "reset": bool(config_value & 0x8000),
            "avg": (config_value >> 9) & 0x07,
            "vbus_ct": (config_value >> 6) & 0x07,
            "vsh_ct": (config_value >> 3) & 0x07,
            "mode": config_value & 0x07,
        }

        return config

    def set_config(self, avg=0, vbus_ct=4, vsh_ct=4, mode=7):
        """
        Set the configuration of the INA226 sensor.

        Args:
            avg (int): Averaging Mode. Bits 9-11 determine the number of samples that are collected and averaged.
            Combinations:
                0: 1    (default)
                1: 4
                2: 16
                3: 64
                4: 128
                5: 256
                6: 512
                7: 1024

            vbus_ct (int): Bus Voltage Conversion Time. Bits 6-8 set the conversion time for the bus voltage measurement.
            Combinations:
                0: 140 µs
                1: 204 µs
                2: 332 µs
                3: 588 µs
                4: 1.1 ms   (default)
                5: 2.116 ms
                6: 4.156 ms
                7: 8.244 ms

            vsh_ct (int): Shunt Voltage Conversion Time. Bits 3-5 set the conversion time for the shunt voltage measurement.
            Combinations:
                0: 140 µs
                1: 204 µs
                2: 332 µs
                3: 588 µs
                4: 1.1 ms   (default)
                5: 2.116 ms
                6: 4.156 ms
                7: 8.244 ms

            mode (int): Operating Mode. Bits 0-2 select continuous, triggered, or power-down mode of operation.
            These bits default to continuous shunt and bus measurement mode.
            Combinations:
                0: Power-Down (or Shutdown)
                1: Shunt Voltage, Triggered
                2: Bus Voltage, Triggered
                3: Shunt and Bus, Triggered
                4: Power-Down (or Shutdown)
                5: Shunt Voltage, Continuous
                6: Bus Voltage, Continuous
                7: Shunt and Bus, Continuous    (default)

        Returns:
            int: Result code (0 for success, -1 for failure).
        """
        # Calculate the value to write to the CONFIG_REG
        config_value = 0
        config_value |= (avg & 0x07) << 9
        config_value |= (vbus_ct & 0x07) << 6
        config_value |= (vsh_ct & 0x07) << 3
        config_value |= mode & 0x07

        # Write the value to the CONFIG_REG
        return self.i2c_write_word(self.CONFIG_REG, config_value)

    def get_shunt_voltage(self):
        """
        Get the shunt voltage in microvolts.

        Returns:
            float: Shunt voltage in microvolts(uV).
        """
        raw_data = self.i2c_read_word(self.SHUNT_VOLTAGE_REG)

        if raw_data > 0x7FFF:
            raw_data = 0x7FFF - raw_data

        voltage = raw_data * 2.5  # Convert raw data to voltage (uV)
        return voltage

    def get_bus_voltage(self):
        """
        Get the bus voltage in millivolts.

        Returns:
            float: Bus voltage in millivolts(mV).
        """
        raw_data = self.i2c_read_word(self.BUS_VOLTAGE_REG)
        voltage = raw_data * 1.25  # Convert raw data to voltage (mV)
        return voltage

    def get_power(self):
        """
        Get the power consumption in milliwatts.

        Returns:
            float: Power consumption in milliwatts.
        """
        raw_data = self.i2c_read_word(self.POWER_REG)
        power = raw_data * 62.5 / self.r_shunt  # Convert raw data to power (mA)
        return power

    def get_current(self):
        """
        Get the current draw in microamps.

        Returns:
            float: Current draw in microamps(uA).
        """
        raw_data = self.i2c_read_word(self.CURRENT_REG)
        current = raw_data * 2500 / self.r_shunt  # Convert raw data to current (uA)
        return current

    def get_calibration(self):
        """
        Get the calibration value from the CALIBRATION_REG register.

        Returns:
            int: The calibration value as a 16-bit integer (hexadecimal).
        """
        return self.i2c_read_word(self.CALIBRATION_REG)

    def set_calibration(self, calibration):
        """
        Set the calibration for the INA226 sensor.

        Args:
            calibration (int): A float value representing the calibration factor to be applied to the raw data.
        Returns:
            int: Result code (0 for success, -1 for failure).
        """
        return self.i2c_write_word(self.CALIBRATION_REG, calibration)

    def get_mask_enable(self):
        """
        Get the settings of the Mask/Enable Register.

        Returns:
            dict: A dictionary containing the mask/enable settings.
            - "SOL" (bool): Shunt Voltage Over-Voltage enabled.
            - "SUL" (bool): Shunt Voltage Under-Voltage enabled.
            - "BOL" (bool): Bus Voltage Over-Voltage enabled.
            - "BUL" (bool): Bus Voltage Under-Voltage enabled.
            - "POL" (bool): Power Over-Limit enabled.
            - "CNVR" (bool): Conversion Ready enabled.
            - "AFF" (bool): Alert Function Flag.
            - "CVRF" (bool): Conversion Ready Flag.
            - "OVF" (bool): Math Overflow Flag.
            - "APOL" (bool): Alert Polarity (inverted or normal).
            - "LEN" (bool): Alert Latch Enable (Latch or Transparent).
        """
        mask_enable = self.i2c_read_word(self.MASK_ENABLE_REG)

        settings = {
            "SOL": bool(mask_enable & 0x8000),
            "SUL": bool(mask_enable & 0x4000),
            "BOL": bool(mask_enable & 0x2000),
            "BUL": bool(mask_enable & 0x1000),
            "POL": bool(mask_enable & 0x0800),
            "CNVR": bool(mask_enable & 0x0400),
            "AFF": bool(mask_enable & 0x0010),
            "CVRF": bool(mask_enable & 0x0008),
            "OVF": bool(mask_enable & 0x0004),
            "APOL": bool(mask_enable & 0x0002),
            "LEN": bool(mask_enable & 0x0001),
        }

        return settings

    def set_mask_enable(self, bit_name):
        """
        Enable a specific function in the Mask/Enable Register.

        Args:
            bit_name (str): The name of the bit to enable. Valid bit names are:
            - 'SOL': Shunt Voltage Over-Voltage
            - 'SUL': Shunt Voltage Under-Voltage
            - 'BOL': Bus Voltage Over-Voltage
            - 'BUL': Bus Voltage Under-Voltage
            - 'POL': Power Over-Limit
            - 'CNVR': Conversion Ready
            - 'AFF': Alert Function Flag
            - 'CVRF': CVRF (Conversion Ready Flag)
            - 'OVF': Math Overflow Flag
            - 'APOL': Alert Polarity
            - 'LEN': Alert Latch Enable

        Returns:
            int: Result code (0 for success, -1 for failure).
        """
        # 定义每个位的名称和对应的位值
        bit_values = {
            "SOL": 0x8000,  # Shunt Voltage Over-Voltage
            "SUL": 0x4000,  # Shunt Voltage Under-Voltage
            "BOL": 0x2000,  # Bus Voltage Over-Voltage
            "BUL": 0x1000,  # Bus Voltage Under-Voltage
            "POL": 0x0800,  # Power Over-Limit
            "CNVR": 0x0400,  # Conversion Ready
            "AFF": 0x0010,  # Alert Function Flag
            "CVRF": 0x0008,  # CVRF (Conversion Ready Flag)
            "OVF": 0x0004,  # Math Overflow Flag
            "APOL": 0x0002,  # Alert Polarity
            "LEN": 0x0001,  # Alert Latch Enable
        }

        # 检查输入的位名是否有效
        if bit_name in bit_values:
            # 获取位值
            bit_value = bit_values[bit_name]
            # 写入 Mask/Enable 寄存器
            return self.i2c_write_word(self.MASK_ENABLE_REG, bit_value)
        else:
            print(f"Invalid bit name: {bit_name}")
            return -1

    def get_alert_limit(self):
        """
        Get the value from the Alert Limit Register.

        Returns:
            int: The value from the Alert Limit Register.
        """
        return self.i2c_read_word(self.ALERT_LIMIT_REG)

    def set_alert_limit(self, value):
        """
        Set the value in the Alert Limit Register.

        Args:
            value (int): The value to be set in the Alert Limit Register.

        Returns:
            int: Result code (0 for success, -1 for failure).
        """
        return self.i2c_write_word(self.ALERT_LIMIT_REG, value)

    def get_manufacturer_id(self):
        """
        Read the manufacturer ID.

        Returns:
            int: Manufacturer ID value.
        """
        return self.i2c_read_word(self.MANUFACTURER_ID_REG)

    def get_die_id(self):
        """
        Read the die ID.

        Returns:
            int: Die ID value.
        """
        return self.i2c_read_word(self.DIE_ID_REG)

    def close(self):
        """
        Close the CH347 device.
        """
        self.driver.close_device()


if __name__ == "__main__":
    sensor = INA226()
    print(sensor.get_config())
    # sensor.reset()
    sensor.set_alert_limit(0x1000)
    print(sensor.get_calibration())
    print(sensor.get_shunt_voltage(), "uV")
    print(sensor.get_bus_voltage(), "mV")
    print(sensor.get_current(), "uA")
    print(sensor.get_power(), "mW")
    # sensor.set_mask_enable('SOL')
    # print(sensor.get_mask_enable())
    print(hex(sensor.get_manufacturer_id()))
    print(hex(sensor.get_die_id()))
    sensor.set_config()
    sensor.close()
