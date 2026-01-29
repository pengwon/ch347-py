import ctypes
from typing import List


class DeviceInfo(ctypes.Structure):
    MAX_PATH = 260
    _fields_ = [
        ("DeviceIndex", ctypes.c_ubyte),  # 当前打开序号
        ("DevicePath", ctypes.c_char * MAX_PATH),  # 设备路径
        (
            "UsbClass",
            ctypes.c_ubyte,
        ),  # USB设备类别: 0=CH341 Vendor; 1=CH347 Vendor; 2=HID
        ("FuncType", ctypes.c_ubyte),  # 设备功能类型: 0=UART1; 1=SPI+I2C; 2=JTAG+I2C
        ("DeviceID", ctypes.c_char * 64),  # USB设备ID: USB\VID_xxxx&PID_xxxx
        (
            "ChipMode",
            ctypes.c_ubyte,
        ),  # 芯片模式: 0=Mode0(UART*2); 1=Mode1(Uart1+SPI+I2C); 2=Mode2(HID Uart1+SPI+I2C); 3=Mode3(Uart1+Jtag+I2C)
        ("DevHandle", ctypes.c_void_p),  # 设备句柄
        ("BulkOutEndpMaxSize", ctypes.c_ushort),  # 上传端点大小
        ("BulkInEndpMaxSize", ctypes.c_ushort),  # 下传端点大小
        ("UsbSpeedType", ctypes.c_ubyte),  # USB速度类型: 0=FS; 1=HS; 2=SS
        ("CH347IfNum", ctypes.c_ubyte),  # USB接口号
        ("DataUpEndp", ctypes.c_ubyte),  # 端点地址
        ("DataDnEndp", ctypes.c_ubyte),  # 端点地址
        ("ProductString", ctypes.c_char * 64),  # USB产品字符串
        ("ManufacturerString", ctypes.c_char * 64),  # USB厂商字符串
        ("WriteTimeout", ctypes.c_ulong),  # USB写超时
        ("ReadTimeout", ctypes.c_ulong),  # USB读超时
        ("FuncDescStr", ctypes.c_char * 64),  # 接口功能描述符
        ("FirmwareVer", ctypes.c_ubyte),  # 固件版本
    ]


class SPIConfig(ctypes.Structure):
    _fields_ = [
        ("Mode", ctypes.c_ubyte),  # 0-3: SPI Mode0/1/2/3
        (
            "Clock",
            ctypes.c_ubyte,
        ),  # 0=60MHz, 1=30MHz, 2=15MHz, 3=7.5MHz, 4=3.75MHz, 5=1.875MHz, 6=937.5KHz, 7=468.75KHz
        ("ByteOrder", ctypes.c_ubyte),  # 0=LSB first(LSB), 1=MSB first(MSB)
        (
            "SPIWriteReadInterval",
            ctypes.c_ushort,
        ),  # Regular interval for SPI read/write commands, in microseconds
        (
            "SPIOutDefaultData",
            ctypes.c_ubyte,
        ),  # Default output data when reading from SPI
        (
            "ChipSelect",
            ctypes.c_ulong,
        ),  # Chip select control. Bit 7 as 0 ignores chip select control,
        # Bit 7 as 1 makes the parameters valid:
        # Bit 1 and Bit 0 as 00/01 selects CS1/CS2 pin as the active low chip select.
        (
            "CS1Polarity",
            ctypes.c_ubyte,
        ),  # Bit 0: CS1 polarity control, 0: active low, 1: active high
        (
            "CS2Polarity",
            ctypes.c_ubyte,
        ),  # Bit 0: CS2 polarity control, 0: active low, 1: active high
        (
            "IsAutoDeactiveCS",
            ctypes.c_ushort,
        ),  # Automatically de-assert chip select after the operation is completed
        (
            "ActiveDelay",
            ctypes.c_ushort,
        ),  # Delay time for executing read/write operations after chip select is set, in microseconds
        (
            "DelayDeactive",
            ctypes.c_ulong,
        ),  # Delay time for executing read/write operations after chip select is de-asserted, in microseconds
    ]


class CH347:
    # MAX devices number
    MAX_DEVICE_NUMBER = 8

    # Define the callback function type
    NOTIFY_ROUTINE = ctypes.CFUNCTYPE(None, ctypes.c_ulong)

    # Define the callback function type
    INTERRUPT_ROUTINE = ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.c_ubyte))

    INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

    def __init__(self, device_index=0, dll_path=None):
        """
        Initialize the CH347 interface.

        Args:
            device_index (int): The index of the device to open (default: 0).
            dll_path (str, optional): Path to the CH347 DLL file. If None, the system will
                                    search for the DLL in system directories.
        """
        if dll_path is None:
            # Let Windows find the DLL in system directories
            self.ch347dll = ctypes.WinDLL("CH347DLLA64")
        else:
            # Use the specified path
            self.ch347dll = ctypes.WinDLL(dll_path)

        self.device_index = device_index

        # 创建回调函数对象并绑定到实例属性
        self.callback_func = self.NOTIFY_ROUTINE(self.event_callback)
        # 创建中断回调函数对象并绑定到实例属性
        self.interrupt_cb_func = self.INTERRUPT_ROUTINE(self.interrupt_callback)
        # 创建回调函数对象并绑定到实例属性
        self.uart_callback_func = self.NOTIFY_ROUTINE(self.uart_event_callback)

        # Set the function argument types and return type for CH347OpenDevice
        self.ch347dll.CH347OpenDevice.argtypes = [ctypes.c_ulong]
        self.ch347dll.CH347OpenDevice.restype = ctypes.c_void_p

        # Set the function argument types and return type for CH347CloseDevice
        self.ch347dll.CH347CloseDevice.argtypes = [ctypes.c_ulong]
        self.ch347dll.CH347CloseDevice.restype = ctypes.c_bool

        # Set the function argument types and return type for CH347GetDeviceInfor
        self.ch347dll.CH347GetDeviceInfor.argtypes = [
            ctypes.c_ulong,
            ctypes.POINTER(DeviceInfo),
        ]
        self.ch347dll.CH347GetDeviceInfor.restype = ctypes.c_bool

        # Set the function argument types and return type for CH347GetVersion
        self.ch347dll.CH347GetVersion.argtypes = [
            ctypes.c_ulong,
            ctypes.POINTER(ctypes.c_ubyte),
            ctypes.POINTER(ctypes.c_ubyte),
            ctypes.POINTER(ctypes.c_ubyte),
            ctypes.POINTER(ctypes.c_ubyte),
        ]
        self.ch347dll.CH347GetVersion.restype = ctypes.c_bool

        # Set the function argument types and return type for CH347SetDeviceNotify
        self.ch347dll.CH347SetDeviceNotify.argtypes = [
            ctypes.c_ulong,
            ctypes.c_char_p,
            ctypes.CFUNCTYPE(None, ctypes.c_ulong),
        ]
        self.ch347dll.CH347SetDeviceNotify.restype = ctypes.c_bool

        # Set the function argument types and return type for CH347ReadData
        self.ch347dll.CH347ReadData.argtypes = [
            ctypes.c_ulong,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_ulong),
        ]
        self.ch347dll.CH347ReadData.restype = ctypes.c_bool

        # Set the function argument types and return type for CH347WriteData
        self.ch347dll.CH347WriteData.argtypes = [
            ctypes.c_ulong,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_ulong),
        ]
        self.ch347dll.CH347WriteData.restype = ctypes.c_bool

        # Set the function argument types and return type for CH347SetTimeout
        self.ch347dll.CH347SetTimeout.argtypes = [
            ctypes.c_ulong,
            ctypes.c_ulong,
            ctypes.c_ulong,
        ]
        self.ch347dll.CH347SetTimeout.restype = ctypes.c_bool

        # Set the function argument types and return type for CH347SPI_Init
        self.ch347dll.CH347SPI_Init.argtypes = [
            ctypes.c_ulong,
            ctypes.POINTER(SPIConfig),
        ]
        self.ch347dll.CH347SPI_Init.restype = ctypes.c_bool

        # Set the function argument types and return type for CH347SPI_GetCfg
        self.ch347dll.CH347SPI_GetCfg.argtypes = [
            ctypes.c_ulong,
            ctypes.POINTER(SPIConfig),
        ]
        self.ch347dll.CH347SPI_GetCfg.restype = ctypes.c_bool

        # Set the function argument types and return type for CH347SPI_ChangeCS
        self.ch347dll.CH347SPI_ChangeCS.argtypes = [ctypes.c_ulong, ctypes.c_ubyte]
        self.ch347dll.CH347SPI_ChangeCS.restype = ctypes.c_bool

        # Set the function argument types and return type for CH347SPI_SetChipSelect
        self.ch347dll.CH347SPI_SetChipSelect.argtypes = [
            ctypes.c_ulong,
            ctypes.c_ushort,
            ctypes.c_ushort,
            ctypes.c_ulong,
            ctypes.c_ulong,
            ctypes.c_ulong,
        ]
        self.ch347dll.CH347SPI_SetChipSelect.restype = ctypes.c_bool

        # Set the function argument types and return type for CH347SPI_Write
        self.ch347dll.CH347SPI_Write.argtypes = [
            ctypes.c_ulong,
            ctypes.c_ulong,
            ctypes.c_ulong,
            ctypes.c_ulong,
            ctypes.c_void_p,
        ]
        self.ch347dll.CH347SPI_Write.restype = ctypes.c_bool

        # Set the function argument types and return type for CH347SPI_Read
        self.ch347dll.CH347SPI_Read.argtypes = [
            ctypes.c_ulong,
            ctypes.c_ulong,
            ctypes.c_ulong,
            ctypes.POINTER(ctypes.c_ulong),
            ctypes.c_void_p,
        ]
        self.ch347dll.CH347SPI_Read.restype = ctypes.c_bool

        # Set the function argument types and return type for CH347SPI_WriteRead
        self.ch347dll.CH347SPI_WriteRead.argtypes = [
            ctypes.c_ulong,
            ctypes.c_ulong,
            ctypes.c_ulong,
            ctypes.c_void_p,
        ]
        self.ch347dll.CH347SPI_WriteRead.restype = ctypes.c_bool

        # Set the function argument types and return type for CH347StreamSPI4
        self.ch347dll.CH347StreamSPI4.argtypes = [
            ctypes.c_ulong,
            ctypes.c_ulong,
            ctypes.c_ulong,
            ctypes.c_void_p,
        ]
        self.ch347dll.CH347StreamSPI4.restype = ctypes.c_bool

        # Set the function argument types and return type for CH347I2C_Set
        self.ch347dll.CH347I2C_Set.argtypes = [ctypes.c_ulong, ctypes.c_ulong]
        self.ch347dll.CH347I2C_Set.restype = ctypes.c_bool

        # Set the function argument types and return type for CH347I2C_SetDelaymS
        self.ch347dll.CH347I2C_SetDelaymS.argtypes = [ctypes.c_ulong, ctypes.c_ulong]
        self.ch347dll.CH347I2C_SetDelaymS.restype = ctypes.c_bool

        # Set the function argument types and return type for CH347StreamI2C
        self.ch347dll.CH347StreamI2C.argtypes = [
            ctypes.c_ulong,
            ctypes.c_ulong,
            ctypes.c_void_p,
            ctypes.c_ulong,
            ctypes.c_void_p,
        ]
        self.ch347dll.CH347StreamI2C.restype = ctypes.c_bool

        self.ch347dll.CH347GPIO_Get.argtypes = [
            ctypes.c_ulong,
            ctypes.POINTER(ctypes.c_ubyte),
            ctypes.POINTER(ctypes.c_ubyte),
        ]
        self.ch347dll.CH347GPIO_Get.restype = ctypes.c_bool

        self.ch347dll.CH347GPIO_Set.argtypes = [
            ctypes.c_ulong,
            ctypes.c_ubyte,
            ctypes.c_ubyte,
            ctypes.c_ubyte,
        ]
        self.ch347dll.CH347GPIO_Set.restype = ctypes.c_bool

        self.ch347dll.CH347SetIntRoutine.argtypes = [
            ctypes.c_ulong,
            ctypes.c_ubyte,
            ctypes.c_ubyte,
            ctypes.c_ubyte,
            ctypes.c_ubyte,
            self.INTERRUPT_ROUTINE,
        ]
        self.ch347dll.CH347SetIntRoutine.restype = ctypes.c_bool

        self.ch347dll.CH347ReadInter.argtypes = [ctypes.c_ulong, ctypes.POINTER(ctypes.c_ubyte)]
        self.ch347dll.CH347ReadInter.restype = ctypes.c_bool

        self.ch347dll.CH347AbortInter.argtypes = [ctypes.c_ulong]
        self.ch347dll.CH347AbortInter.restype = ctypes.c_bool

        self.ch347dll.CH347Uart_Open.argtypes = [ctypes.c_ulong]
        self.ch347dll.CH347Uart_Open.restype = ctypes.c_void_p

        self.ch347dll.CH347Uart_Close.argtypes = [ctypes.c_ulong]
        self.ch347dll.CH347Uart_Close.restype = ctypes.c_bool

        self.ch347dll.CH347Uart_SetDeviceNotify.argtypes = [
            ctypes.c_ulong,
            ctypes.POINTER(ctypes.c_ubyte),
            self.NOTIFY_ROUTINE,
        ]
        self.ch347dll.CH347Uart_SetDeviceNotify.restype = ctypes.c_bool

        self.ch347dll.CH347Uart_GetCfg.argtypes = [
            ctypes.c_ulong,
            ctypes.POINTER(ctypes.c_ulong),
            ctypes.POINTER(ctypes.c_ubyte),
            ctypes.POINTER(ctypes.c_ubyte),
            ctypes.POINTER(ctypes.c_ubyte),
            ctypes.POINTER(ctypes.c_ubyte),
        ]
        self.ch347dll.CH347Uart_GetCfg.restype = ctypes.c_bool

        self.ch347dll.CH347Uart_Init.argtypes = [
            ctypes.c_ulong,
            ctypes.c_uint32,
            ctypes.c_ubyte,
            ctypes.c_ubyte,
            ctypes.c_ubyte,
            ctypes.c_ubyte,
        ]
        self.ch347dll.CH347Uart_Init.restype = ctypes.c_bool

        self.ch347dll.CH347Uart_SetTimeout.argtypes = [
            ctypes.c_ulong,
            ctypes.c_ulong,
            ctypes.c_ulong,
        ]
        self.ch347dll.CH347Uart_SetTimeout.restype = ctypes.c_bool

        self.ch347dll.CH347Uart_Read.argtypes = [
            ctypes.c_ulong,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_ulong),
        ]
        self.ch347dll.CH347Uart_Read.restype = ctypes.c_bool

        self.ch347dll.CH347Uart_Write.argtypes = [
            ctypes.c_ulong,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_ulong),
        ]
        self.ch347dll.CH347Uart_Write.restype = ctypes.c_bool

        self.ch347dll.CH347Uart_QueryBufUpload.argtypes = [
            ctypes.c_ulong,
            ctypes.POINTER(ctypes.c_longlong),
        ]
        self.ch347dll.CH347Uart_QueryBufUpload.restype = ctypes.c_bool

        self.ch347dll.CH347Uart_GetDeviceInfor.argtypes = [
            ctypes.c_ulong,
            ctypes.POINTER(DeviceInfo),
        ]
        self.ch347dll.CH347Uart_GetDeviceInfor.restype = ctypes.c_bool

    def list_devices(self):
        # List all devices
        num_devices = 0
        dev_info = DeviceInfo()
        for i in range(self.MAX_DEVICE_NUMBER):
            if self.ch347dll.CH347OpenDevice(i) == self.INVALID_HANDLE_VALUE:
                break
            num_devices += 1
            if self.ch347dll.CH347GetDeviceInfor(i, ctypes.byref(dev_info)):
                for field_name, _ in dev_info._fields_:
                    value = getattr(dev_info, field_name)
                    print(f"{field_name}: {value}")
            print("-" * 40)
            self.ch347dll.CH347CloseDevice(i)
        print(f"Number of devices: {num_devices}")
        return num_devices

    @staticmethod
    def event_callback(self, event_status):
        # Callback function implementation
        print("Callback event status:", event_status)
        if event_status == 0:
            # Device unplug event
            print("Device unplugged")
        elif event_status == 3:
            # Device insertion event
            print("Device inserted")

    @INTERRUPT_ROUTINE
    def interrupt_callback(self, istatus):
        # Callback function implementation
        # Cast to pointer to array of 8 unsigned bytes
        byte_array = ctypes.cast(istatus, ctypes.POINTER(ctypes.c_ubyte * 8)).contents
        print("Interrupt received:", " ".join(f"0x{b:02X}" for b in byte_array))

    @NOTIFY_ROUTINE
    def uart_event_callback(self, event_status):
        # Callback function implementation
        print("Uart callback event status:", event_status)
        if event_status == 0:
            # Device unplug event
            print("Uart unplugged")
        elif event_status == 3:
            # Device insertion event
            print("Uart inserted")

    def open_device(self):
        """
        Open USB device.

        Returns:
            int: Handle to the opened device if successful, None otherwise.
        """
        handle = self.ch347dll.CH347OpenDevice(self.device_index)
        if handle != self.INVALID_HANDLE_VALUE:
            return handle
        else:
            return None

    def close_device(self):
        """
        Close USB device.

        Returns:
            bool: True if successful, False otherwise.
        """
        result = self.ch347dll.CH347CloseDevice(self.device_index)
        return result

    def get_device_info(self):
        """
        Retrieve the information of the connected device.

        This method uses the device index to call the CH347 DLL and obtain the device's details.

        Returns:
            DeviceInfo: An instance of DeviceInfo with the device details if successful.
            None: If the retrieval fails.
        """
        dev_info = DeviceInfo()
        result = self.ch347dll.CH347GetDeviceInfor(self.device_index, ctypes.byref(dev_info))
        if result:
            return dev_info
        else:
            return None

    def get_version(self):
        """
        Obtain driver version, library version, device version, and chip type.

        This method retrieves various versions related to the CH347 device and returns them as a tuple.

        Returns:
            tuple or None: A tuple containing the following information if successful:
                - driver_ver (int): The driver version.
                - dll_ver (int): The library version.
                - device_ver (int): The device version.
                - chip_type (int): The chip type.
            Returns None if the retrieval fails.
        """
        # Create variables to store the version information
        driver_ver = ctypes.c_ubyte()
        dll_ver = ctypes.c_ubyte()
        device_ver = ctypes.c_ubyte()
        chip_type = ctypes.c_ubyte()

        # Call the CH347GetVersion function
        result = self.ch347dll.CH347GetVersion(
            self.device_index,
            ctypes.byref(driver_ver),
            ctypes.byref(dll_ver),
            ctypes.byref(device_ver),
            ctypes.byref(chip_type),
        )
        if result:
            return driver_ver.value, dll_ver.value, device_ver.value, chip_type.value
        else:
            return None

    def set_device_notify(self, device_id, notify_routine=event_callback):
        """
        Configure device event notifier.

        Args:
            device_id (str): Optional parameter specifying the ID of the monitored device.
            notify_routine (callable): Callback function to handle device events.

        Returns:
            bool: True if successful, False otherwise.
        """
        callback = self.NOTIFY_ROUTINE(notify_routine)
        result = self.ch347dll.CH347SetDeviceNotify(self.device_index, device_id, callback)
        return result

    def read_data(self, buffer, length):
        """
        Read USB data block.

        Args:
            buffer (ctypes.c_void_p): Pointer to a buffer to store the read data.
            length (ctypes.POINTER(ctypes.c_ulong)): Pointer to the length unit. Contains the length to be read as input and the actual read length after return.

        Returns:
            bool: True if successful, False otherwise.
        """
        result = self.ch347dll.CH347ReadData(self.device_index, buffer, length)
        return result

    def write_data(self, buffer, length):
        """
        Write USB data block.

        Args:
            buffer (ctypes.c_void_p): Pointer to a buffer containing the data to be written.
            length (ctypes.POINTER(ctypes.c_ulong)): Pointer to the length unit. Input length is the intended length, and the return length is the actual length.

        Returns:
            bool: True if successful, False otherwise.
        """
        result = self.ch347dll.CH347WriteData(self.device_index, buffer, length)
        return result

    def set_timeout(self, write_timeout, read_timeout):
        """
        Set the timeout of USB data read and write.

        Args:
            write_timeout (int): Timeout for USB to write data blocks, in milliseconds. Use 0xFFFFFFFF to specify no timeout (default).
            read_timeout (int): Timeout for USB to read data blocks, in milliseconds. Use 0xFFFFFFFF to specify no timeout (default).

        Returns:
            bool: True if successful, False otherwise.
        """
        result = self.ch347dll.CH347SetTimeout(self.device_index, write_timeout, read_timeout)
        return result

    def spi_init(self, spi_config: SPIConfig) -> bool:
        """
        Initialize the SPI Controller.

        Args:
            spi_config (SPIConfig): The configuration for the SPI controller.

        Returns:
            bool: True if initialization is successful, False otherwise.
        """
        result = self.ch347dll.CH347SPI_Init(self.device_index, ctypes.byref(spi_config))
        return result

    def spi_get_config(self):
        """
        Retrieves the SPI controller configuration information.

        Returns:
            SPIConfig: An instance of the SPIConfig class containing the configuration information
            if the operation was successful. If the operation failed, returns None.

        The returned SPIConfig object will contain the configuration details retrieved from the SPI
        controller if the operation was successful. Otherwise, it will be None.
        """
        spi_config = SPIConfig()
        result = self.ch347dll.CH347SPI_GetCfg(self.device_index, ctypes.byref(spi_config))
        if result:
            return spi_config
        else:
            return None

    def spi_change_cs(self, status):
        """
        Change the chip selection status.

        Args:
            status (int): Chip selection status. 0 = Cancel the piece to choose, 1 = Set piece selected.

        Returns:
            bool: True if successful, False otherwise.
        """
        result = self.ch347dll.CH347SPI_ChangeCS(self.device_index, status)
        return result

    def spi_set_chip_select(
        self,
        enable_select,
        chip_select,
        is_auto_deactive_cs,
        active_delay,
        delay_deactive,
    ):
        """
        Set SPI chip selection.

        Args:
            enable_select (int): Enable selection status. The lower octet is CS1 and the higher octet is CS2.
                                A byte value of 1 sets CS, 0 ignores this CS setting.
            chip_select (int): Chip selection status. The lower octet is CS1 and the higher octet is CS2.
                               A byte value of 1 sets CS, 0 ignores this CS setting.
            is_auto_deactive_cs (int): Auto deactivation status. The lower 16 bits are CS1 and the higher 16 bits are CS2.
                                       Whether to undo slice selection automatically after the operation is complete.
            active_delay (int): Latency of read/write operations after chip selection, in microseconds.
                                The lower 16 bits are CS1 and the higher 16 bits are CS2.
            delay_deactive (int): Delay time for read and write operations after slice selection, in microseconds.
                                  The lower 16 bits are CS1 and the higher 16 bits are CS2.

        Returns:
            bool: True if successful, False otherwise.
        """
        result = self.ch347dll.CH347SPI_SetChipSelect(
            self.device_index,
            enable_select,
            chip_select,
            is_auto_deactive_cs,
            active_delay,
            delay_deactive,
        )
        return result

    def spi_write(self, chip_select: int, write_data: List[int], write_step: int = 512) -> bool:
        """
        SPI write data.

        Args:
            chip_select (int): Chip selection control. When bit 7 is 0, chip selection control is ignored.
                                When bit 7 is 1, chip selection operation is performed.
            write_data (List[int]): List of integers to write.
            write_step (int, optional): The length of a single block to be read. Default is 512.

        Returns:
            bool: True if successful, False otherwise.
        """
        write_length = len(write_data)
        write_buffer = ctypes.create_string_buffer(bytes(write_data))
        result = self.ch347dll.CH347SPI_Write(
            self.device_index, chip_select, write_length, write_step, write_buffer
        )
        return result

    def spi_read(self, chip_select: int, write_data: List[int], read_length: int) -> List[int]:
        """
        SPI read data.

        Args:
            chip_select (int): Chip selection control. When bit 7 is 0, chip selection control is ignored.
                            When bit 7 is 1, chip selection operation is performed.
            write_data (List[int]): List of integers to write.
            read_length (int): Number of bytes to read.

        Returns:
            List[int]: Data read in from the SPI stream if successful, None otherwise.
        """
        write_length = len(write_data)

        # Create ctypes buffer for write data
        write_buffer = ctypes.create_string_buffer(bytes(write_data))

        # Create ctypes buffer for read data
        read_buffer = ctypes.create_string_buffer(read_length)

        # Create combined buffer for read and write data
        combined_buffer = ctypes.create_string_buffer(
            write_buffer.raw[:write_length] + read_buffer.raw
        )

        result = self.ch347dll.CH347SPI_Read(
            self.device_index,
            chip_select,
            write_length,
            ctypes.byref(ctypes.c_ulong(read_length)),
            combined_buffer,
        )

        if result:
            # Extract the read data from the combined buffer
            read_data = list(combined_buffer[:read_length])
            return read_data
        else:
            return None

    def spi_write_read(self, chip_select, length, io_buffer):
        """
        Handle SPI data stream 4-wire interface.

        Args:
            chip_select (int): Selection control. If the film selection control bit 7 is 0, ignore the film selection control.
                               If bit 7 is 1, perform the film selection.
            length (int): Number of bytes of data to be transferred.
            io_buffer (ctypes.c_void_p): Points to a buffer that places the data to be written out from DOUT.
                                        Returns the data read in from DIN.

        Returns:
            bool: True if successful, False otherwise.
        """
        result = self.ch347dll.CH347SPI_WriteRead(self.device_index, chip_select, length, io_buffer)
        return result

    def stream_spi4(self, chip_select, length, io_buffer):
        """
        Handle SPI data stream 4-wire interface.

        Args:
            chip_select (int): Film selection control. If bit 7 is 0, slice selection control is ignored.
                               If bit 7 is 1, the parameter is valid: Bit 1 bit 0 is 00/01/10.
                               Select D0/D1/D2 pins as low-level active chip options, respectively.
            length (int): Number of bytes of data to be transferred.
            io_buffer (ctypes.c_void_p): Points to a buffer that places data to be written out from DOUT.
                                        Returns data to be read in from DIN.

        Returns:
            bool: True if successful, False otherwise.
        """
        result = self.ch347dll.CH347StreamSPI4(self.device_index, chip_select, length, io_buffer)
        return result

    def i2c_set(self, interface_speed):
        """
        Set the serial port flow mode.

        Args:
            interface_speed (int): I2C interface speed / SCL frequency. Bit 1-bit 0:
                                0 = low speed / 20KHz
                                1 = standard / 100KHz (default)
                                2 = fast / 400KHz
                                3 = high speed / 750KHz

        Returns:
            bool: True if successful, False otherwise.
        """
        result = self.ch347dll.CH347I2C_Set(self.device_index, interface_speed)
        return result

    def i2c_set_delay_ms(self, delay_ms):
        """
        Set the hardware asynchronous delay to a specified number of milliseconds before the next stream operation.

        Args:
            delay_ms (int): Delay duration in milliseconds (ms).

        Returns:
            bool: True if successful, False otherwise.
        """
        result = self.ch347dll.CH347I2C_SetDelaymS(self.device_index, delay_ms)
        return result

    def stream_i2c(self, write_data, read_length):
        """
        Process I2C data stream.

        Args:
            write_data (bytes): Data to write. The first byte is usually the I2C device address and read/write direction bit.
            read_length (int): Number of bytes of data to read.

        Returns:
            bytes: Data read from the I2C stream.
        """
        write_length = len(write_data)

        # Convert write_data to ctypes buffer
        write_buffer = ctypes.create_string_buffer(bytes(write_data))

        # Create ctypes buffer for read data
        read_buffer = ctypes.create_string_buffer(read_length)

        result = self.ch347dll.CH347StreamI2C(
            self.device_index, write_length, write_buffer, read_length, read_buffer
        )

        if result:
            return read_buffer[:read_length]
        else:
            return None

    def spi_set_frequency(self, spi_speed_hz: int) -> bool:
        """
        Set the SPI clock frequency.

        After calling this interface, you need to call spi_init again for reinitialization.

        Args:
            spi_speed_hz (int): Set the SPI clock frequency in Hz.

        Returns:
            bool: True if successful, False otherwise.
        """
        # Set the function argument types and return type if not already set
        if not hasattr(self.ch347dll.CH347SPI_SetFrequency, "argtypes"):
            self.ch347dll.CH347SPI_SetFrequency.argtypes = [
                ctypes.c_ulong,
                ctypes.c_ulong,
            ]
            self.ch347dll.CH347SPI_SetFrequency.restype = ctypes.c_bool

        result = self.ch347dll.CH347SPI_SetFrequency(self.device_index, spi_speed_hz)
        return result

    def spi_set_data_bits(self, data_bits: int) -> bool:
        """
        Set the SPI data bits (only supported by CH347F).

        Args:
            data_bits (int): 0=8bit, 1=16bit

        Returns:
            bool: True if successful, False otherwise.
        """
        # Set the function argument types and return type if not already set
        if not hasattr(self.ch347dll.CH347SPI_SetDataBits, "argtypes"):
            self.ch347dll.CH347SPI_SetDataBits.argtypes = [
                ctypes.c_ulong,
                ctypes.c_ubyte,
            ]
            self.ch347dll.CH347SPI_SetDataBits.restype = ctypes.c_bool

        result = self.ch347dll.CH347SPI_SetDataBits(self.device_index, data_bits)
        return result

    def get_serial_number(self) -> str:
        """
        Get the USB serial number of the device.

        Returns:
            str: The device serial number if successful, None otherwise.
        """
        # Set the function argument types and return type if not already set
        if not hasattr(self.ch347dll.CH347GetSerialNumber, "argtypes"):
            self.ch347dll.CH347GetSerialNumber.argtypes = [
                ctypes.c_ulong,
                ctypes.c_char_p,
            ]
            self.ch347dll.CH347GetSerialNumber.restype = ctypes.c_bool

        # Create a buffer for the serial number
        serial_number = ctypes.create_string_buffer(64)

        result = self.ch347dll.CH347GetSerialNumber(
            self.device_index,
            serial_number,
        )

        if result:
            return serial_number.value.decode("utf-8")
        else:
            return None

    def get_chip_type(self) -> int:
        """
        Get the CH347 chip type.

        Returns:
            int: 0=CHIP_TYPE_CH341, 1=CHIP_TYPE_CH347/CHIP_TYPE_CH347T,
                2=CHIP_TYPE_CH347F, 3=CHIP_TYPE_CH339W
        """
        # Set the function argument types and return type if not already set
        if not hasattr(self.ch347dll.CH347GetChipType, "argtypes"):
            self.ch347dll.CH347GetChipType.argtypes = [ctypes.c_ulong]
            self.ch347dll.CH347GetChipType.restype = ctypes.c_ubyte

        result = self.ch347dll.CH347GetChipType(self.device_index)
        return result

    def i2c_set_stretch(self, enable: bool) -> bool:
        """
        Set I2C Clock Stretch.

        Args:
            enable (bool): I2C Clock Stretch enable, True=enable, False=disable

        Returns:
            bool: True if successful, False otherwise.
        """
        # Set the function argument types and return type if not already set
        if not hasattr(self.ch347dll.CH347I2C_SetStretch, "argtypes"):
            self.ch347dll.CH347I2C_SetStretch.argtypes = [
                ctypes.c_ulong,
                ctypes.c_bool,
            ]
            self.ch347dll.CH347I2C_SetStretch.restype = ctypes.c_bool

        result = self.ch347dll.CH347I2C_SetStretch(self.device_index, enable)
        return result

    def i2c_set_driver_mode(self, mode: int) -> bool:
        """
        Set the I2C pins drive mode.

        Args:
            mode (int): 0=open-drain mode, 1=push-pull mode

        Returns:
            bool: True if successful, False otherwise.
        """
        # Set the function argument types and return type if not already set
        if not hasattr(self.ch347dll.CH347I2C_SetDriverMode, "argtypes"):
            self.ch347dll.CH347I2C_SetDriverMode.argtypes = [
                ctypes.c_ulong,
                ctypes.c_ubyte,
            ]
            self.ch347dll.CH347I2C_SetDriverMode.restype = ctypes.c_bool

        result = self.ch347dll.CH347I2C_SetDriverMode(self.device_index, mode)
        return result

    def stream_i2c_ret_ack(self, write_data, read_length) -> tuple:
        """
        Process I2C data stream, 2-wire interface, and return the number of ACK obtained by the host side.

        Args:
            write_data (bytes): Data to write. The first byte is usually the I2C device address and read/write direction bit.
            read_length (int): Number of bytes of data to read.

        Returns:
            tuple: (bool, bytes, int) - A tuple containing:
                - bool: True if successful, False otherwise
                - bytes: Data read from the I2C stream
                - int: The number of ACK values returned by read/write
        """
        # Set the function argument types and return type if not already set
        if not hasattr(self.ch347dll.CH347StreamI2C_RetACK, "argtypes"):
            self.ch347dll.CH347StreamI2C_RetACK.argtypes = [
                ctypes.c_ulong,
                ctypes.c_ulong,
                ctypes.c_void_p,
                ctypes.c_ulong,
                ctypes.c_void_p,
                ctypes.POINTER(ctypes.c_ulong),
            ]
            self.ch347dll.CH347StreamI2C_RetACK.restype = ctypes.c_bool

        write_length = len(write_data)

        # Convert write_data to ctypes buffer
        write_buffer = ctypes.create_string_buffer(bytes(write_data))

        # Create ctypes buffer for read data
        read_buffer = ctypes.create_string_buffer(read_length)

        # Create a variable to store the ACK count
        ack_count = ctypes.c_ulong(0)

        result = self.ch347dll.CH347StreamI2C_RetACK(
            self.device_index,
            write_length,
            write_buffer,
            read_length,
            read_buffer,
            ctypes.byref(ack_count),
        )

        if result:
            return result, read_buffer[:read_length], ack_count.value
        else:
            return result, None, 0

    def read_eeprom(self, eeprom_id: int, addr: int, length: int) -> bytes:
        """
        Reads data blocks from EEPROM.

        Args:
            eeprom_id (int): EEPROM model ID (see EEPROM_TYPE enum in header file).
            addr (int): The address of data unit.
            length (int): Number of bytes of data to be read.

        Returns:
            bytes: The data read from the EEPROM if successful, None otherwise.
        """
        # Set the function argument types and return type if not already set
        if not hasattr(self.ch347dll.CH347ReadEEPROM, "argtypes"):
            self.ch347dll.CH347ReadEEPROM.argtypes = [
                ctypes.c_ulong,
                ctypes.c_int,  # EEPROM_TYPE enum
                ctypes.c_ulong,
                ctypes.c_ulong,
                ctypes.POINTER(ctypes.c_ubyte),
            ]
            self.ch347dll.CH347ReadEEPROM.restype = ctypes.c_bool

        # Create a buffer for the data
        buffer = (ctypes.c_ubyte * length)()

        result = self.ch347dll.CH347ReadEEPROM(
            self.device_index,
            eeprom_id,
            addr,
            length,
            buffer,
        )

        if result:
            return bytes(buffer)
        else:
            return None

    def write_eeprom(self, eeprom_id: int, addr: int, data: bytes) -> bool:
        """
        Writes a data block to the EEPROM.

        Args:
            eeprom_id (int): EEPROM model ID (see EEPROM_TYPE enum in header file).
            addr (int): The address of data unit.
            data (bytes): Data to be written.

        Returns:
            bool: True if successful, False otherwise.
        """
        # Set the function argument types and return type if not already set
        if not hasattr(self.ch347dll.CH347WriteEEPROM, "argtypes"):
            self.ch347dll.CH347WriteEEPROM.argtypes = [
                ctypes.c_ulong,
                ctypes.c_int,  # EEPROM_TYPE enum
                ctypes.c_ulong,
                ctypes.c_ulong,
                ctypes.POINTER(ctypes.c_ubyte),
            ]
            self.ch347dll.CH347WriteEEPROM.restype = ctypes.c_bool

        length = len(data)

        # Convert data to ctypes buffer
        buffer = (ctypes.c_ubyte * length)(*data)

        result = self.ch347dll.CH347WriteEEPROM(
            self.device_index,
            eeprom_id,
            addr,
            length,
            buffer,
        )

        return result

    #####################################################################
    #
    #  GPIO Interfaces
    #
    #####################################################################

    def gpio_get(self, io_dir, io_data):
        """
        Get GPIO Direction and Pin Level of CH347

        Args:
            index (int):               Specifies the device index.
            io_dir (ctypes.c_void_p):  GPIO direction: bits 0–7 correspond to GPIO0–GPIO7. 0 = input; 1 = output.
            io_data (ctypes.c_void_p): GPIO level: bits 0–7 correspond to GPIO0–GPIO7. 0 = low level; 1 = high level.
        """
        dir_val = ctypes.c_ubyte(0)
        data_val = ctypes.c_ubyte(0)
        result = self.ch347dll.CH347GPIO_Get(
            self.device_index, ctypes.byref(dir_val), ctypes.byref(data_val)
        )
        io_dir[0] = dir_val.value
        io_data[0] = data_val.value
        return result

    def gpio_set(self, io_mask, io_dir, io_data):
        """
        Get the GPIO direction and pin level values of CH347.

        Args:
            index (int): Specifies the device index.
            io_mask (int): Data valid mask: bits 0-7 correspond to GPIO0-7.
            io_dir (int): Sets the I/O direction; if a bit is 0, the corresponding pin is input; if a bit is 1, the corresponding pin is output. GPIO0-7 correspond to bits 0-7.
            io_data (int): Output data; if the I/O direction is output, then when a bit is 0, the corresponding pin outputs a low level; when a bit is 1, it outputs a high level.
        """
        result = self.ch347dll.CH347GPIO_Set(self.device_index, io_mask, io_dir, io_data)
        return result

    def set_interrupt(
        self, int0_pin, int0_mode, int1_pin, int1_mode, interrupt_callback_func=interrupt_callback
    ):
        """
        Set CH347 GPIO Interrupt Service Routine

        Args:
            int0_pin (int): Interrupt GPIO pin number 0-7 or >7 to disable
            int0_mode (int): Interrupt mode for int0 (0=falling,1=rising,2=both,3=reserved)
            int1_pin (int): Interrupt GPIO pin number 0-7 or >7 to disable
            int1_mode (int): Interrupt mode for int1 (same as int0_mode)
            interrupt_callback_func (callable or None): Callback function or None to disable ISR

        Returns:
            bool: True if successful, False otherwise
        """

        if interrupt_callback_func is None:
            # Create a NULL callback pointer to disable interrupt
            self.interrupt_cb_func = ctypes.cast(0, self.INTERRUPT_ROUTINE)
        else:
            # Wrap the Python callback with the C function prototype
            self.interrupt_cb_func = self.INTERRUPT_ROUTINE(interrupt_callback_func)

        result = self.ch347dll.CH347SetIntRoutine(
            self.device_index, int0_pin, int0_mode, int1_pin, int1_mode, self.interrupt_cb_func
        )
        return result

    def read_interrupt_status(self, istatus):
        """
        This function is used to read interrupt data
        Args:
            iIndex:  Specifies the device index to operate on
            iStatus: Pointer to a byte used to store the read GPIO pin status data; refer to the bit description below
        Returns:
            bool: Returns True if successful, False otherwise.
        """
        # Create a buffer for the serial number
        int_val = (ctypes.c_ubyte * 8)()
        # result = self.ch347dll.CH347ReadInter(self.device_index, int_val)
        result = False
        print("there is error for this function")
        istatus[:] = list(int_val)
        return result

    def abort_interrupt(self):
        """
        Cancel GPIO Interrupt Service
        Returns:
            bool: Returns True if successful, False otherwise.
        """
        return self.ch347dll.CH347AbortInter(self.device_index)

    #####################################################################
    #
    #  Uart Interface
    #
    #####################################################################

    def uart_open(self):
        """
        Open serial port
        """

        handle = self.ch347dll.CH347Uart_Open(self.device_index)
        if handle != self.INVALID_HANDLE_VALUE:
            return handle
        else:
            return None

    def uart_close(self):
        """
        Close serial port
        """
        result = self.ch347dll.CH347Uart_Close(self.device_index)
        return result

    def uart_set_notify(self, device_id, uart_notify_routine=uart_event_callback):
        """
        Set the device event notification program
        """
        ######################################################
        #
        # Not tested yet
        #
        ######################################################

        if uart_notify_routine is None:
            # Create a NULL callback pointer to disable interrupt
            self.uart_callback_func = ctypes.cast(0, self.NOTIFY_ROUTINE)
        else:
            # Wrap the Python callback with the C function prototype
            self.uart_callback_func = self.NOTIFY_ROUTINE(uart_notify_routine)

        result = self.ch347dll.CH347Uart_SetDeviceNotify(
            self.device_index, device_id, self.uart_callback_func
        )
        return result

    def uart_getcfg(self, baudrate, bytesize, parity, stopbits, timeout):
        """
        Obtain UART hardware configuration
        """
        ######################################################
        #
        # Tested, seems not working
        #
        ######################################################
        baudrate_val = ctypes.c_ulong(1)
        bytesize_val = ctypes.c_ubyte(1)
        parity_val = ctypes.c_ubyte(1)
        stopbits_val = ctypes.c_ubyte(1)
        timeout_val = ctypes.c_ubyte(1)
        result = self.ch347dll.CH347Uart_GetCfg(
            self.device_index,
            ctypes.byref(baudrate_val),
            ctypes.byref(bytesize_val),
            ctypes.byref(parity_val),
            ctypes.byref(stopbits_val),
            ctypes.byref(timeout_val),
        )
        baudrate[0] = baudrate_val.value
        bytesize[0] = bytesize_val.value
        parity[0] = parity_val.value
        stopbits[0] = stopbits_val.value
        timeout[0] = timeout_val.value

        return result

    def uart_init(self, baudrate, bytesize, parity, stopbits, timeout):
        """
        Set UART configuration
        """
        result = self.ch347dll.CH347Uart_Init(
            self.device_index, baudrate, bytesize, parity, stopbits, timeout
        )
        return result

    def uart_set_timeout(self, write_timeout, read_timeout):
        """
        Set the timeout of USB data read and write
        """
        result = self.ch347dll.CH347Uart_SetTimeout(self.device_index, write_timeout, read_timeout)
        return result

    def uart_read(self, io_buffer, length):
        """
        Read data block
        """
        read_buffer = ctypes.create_string_buffer(length[0])
        length_val = ctypes.c_ulong(length[0])
        result = self.ch347dll.CH347Uart_Read(
            self.device_index, read_buffer, ctypes.byref(length_val)
        )
        ctypes.memmove(io_buffer, read_buffer, length_val.value)
        length[0] = length_val.value
        return result

    def uart_write(self, io_buffer, length):
        """
        Write out blocks of data
        """
        write_buffer = ctypes.create_string_buffer(bytes(io_buffer))
        length_val = ctypes.c_ulong(length[0])
        result = self.ch347dll.CH347Uart_Write(
            self.device_index, write_buffer, ctypes.byref(length_val)
        )
        length[0] = length_val.value
        return result

    def uart_query_buffer_upload(self, remain_bytes):
        """
        Query how many bytes are unfetched in the read buffer
        """
        ######################################################
        #
        # Not tested yet
        #
        ######################################################
        length_val = ctypes.c_longlong()
        result = self.ch347dll.CH347Uart_QueryBufUpload(self.device_index, ctypes.byref(length_val))
        remain_bytes[0] = length_val.value
        return result

    def uart_get_device_info(self):
        """
        Obtaining Device Information
        """
        dev_info = DeviceInfo()
        result = self.ch347dll.CH347Uart_GetDeviceInfor(self.device_index, ctypes.byref(dev_info))
        if result:
            return dev_info
        else:
            return None
