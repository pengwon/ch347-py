# ch347-py

[English](README_en.md)

## 简介

`ch347-py`是一个用于驱动CH347芯片的Python绑定库，支持 Windows 和 Linux。它提供了一种简单的方式来与CH347芯片进行交互，可以基于此开发I2C、SPI等通信接口应用。

## 安装

### 使用pip安装

你可以通过pip来安装这个库：

```bash
pip install ch347-py
```

### 从源码安装

使用uv进行开发（推荐）：

```bash
git clone https://github.com/pengwon/ch347-py.git
cd ch347-py

# 安装uv（如果尚未安装）
pip install uv

# 创建虚拟环境并安装依赖
uv sync

# 激活虚拟环境
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate  # Windows
```

使用传统方式：

```bash
git clone https://github.com/pengwon/ch347-py.git
cd ch347-py
pip install -e .
```

### 开发环境设置

如果你想参与开发或运行测试，需要安装开发依赖：

```bash
# 使用uv（推荐）
uv sync

# 或使用pip
pip install -e ".[dev]"
```

### Linux 环境

ch347-py 在 Linux 上调用沁恒自己发布的动态库，先把它装好：

```bash
git clone https://github.com/WCHSoftGroup/ch341par_linux.git
cd ch341par_linux/driver
make && sudo make install                         # ch34x_pis 内核驱动，生成 /dev/ch34x_pis*

sudo cp ../lib/x64/dynamic/libch347.so /usr/lib   # 另提供 aarch64、arm、mips 版本
sudo ldconfig
```

再放开设备节点权限，让普通用户也能打开：

```bash
echo 'KERNEL=="ch34x_pis*", MODE="0666"' | sudo tee /etc/udev/rules.d/99-ch347.rules
sudo udevadm control --reload-rules
```

`CH347()` 默认打开 `/dev/ch34x_pis0`；芯片工作在 HID 模式，或者要区分多个适配器时，
可以直接给出节点名：`CH347(device_index="/dev/hidraw0")`。

libch347.so 里没有对应实现的接口，在 Linux 下会抛 `NotImplementedError`：

- `set_device_notify`：库不提供插拔事件回调，可以用 udev 监听 `/dev/ch34x_pis*` 的出现与消失。
- `uart_*`：串口功能以 `/dev/tty*` 形式提供，用 pyserial 即可。
- `get_version`、`get_serial_number`、`read_data`、`write_data`、`spi_set_chip_select`、
  `read_interrupt_status`：改用 `get_chip_type`、SPI/I2C 流接口，以及传给 `spi_init`
  的 `SPIConfig`。

`set_interrupt` 可用，但有两点差别：同一时刻只能有一个 GPIO 作为中断源；回调收到的是
全零状态块（内核只送边沿信号），需要引脚电平时用 `gpio_get` 读取。

### 设备插拔通知（Windows）

`set_device_notify` 只有在调用它的线程会派发 Windows 消息时才有效：DLL 会在该线程上创建
一个隐藏的通知窗口，驱动的插拔事件通过这个窗口的消息队列送达。Tk、Qt 这类自带主循环的
程序本来就在派发忙，不用额外处理。控制台程序如果只是 `sleep`，消息永远得不到派发，回调
也就不会响——改用工作线程注册：

```python
def on_event(event_status):
    print("device event:", event_status)

dev = CH347()
dev.start_device_notify(b"vid_1a86\x00", on_event)
# …… 回调在 pump 线程上执行 ……
dev.stop_device_notify()
```

## 使用方法

首先，你需要从`ch347`模块中导入`CH347`类：

```python
from ch347 import CH347
```

然后，你可以创建一个`CH347`类的实例，并使用它的方法来与CH347芯片进行交互。例如：

```python
driver = CH347()
driver.spi_write(0x00, [0xFF] * 10)
```

## 测试

本项目包含了一些测试脚本，你可以运行这些脚本来测试和演示如何使用这个库。

其中两个不需要接上 CH347，它们对着一个假的库对象跑：

```bash
uv run pytest tests/test_callbacks.py tests/test_linux_library.py
```

其余脚本是硬件用例，插上设备后再运行。

## 参考文档

1. [读取MPU6050传感器数据和显示](https://mp.weixin.qq.com/s?__biz=MzA3NzMyNTIyOA==&mid=2651481825&idx=1&sn=bbe2833173dcf0420eaac9faff14ca8b&chksm=84ad7022b3daf9349f8e57e87abacef833bd742f655a60379e07e8ee2529cb012d807a132a92#rd)
2. [读写SPI Flash](https://mp.weixin.qq.com/s?__biz=MzA3NzMyNTIyOA==&mid=2651481820&idx=1&sn=b28a3b59fa7104383ced33ddf9cee7c5&chksm=84ad701fb3daf9099a0245f143c6fc3f5398af3657cf028e052fa3ad944aa510730fee319fa8#rd)
3. [连接MPU6050](https://mp.weixin.qq.com/s?__biz=MzA3NzMyNTIyOA==&mid=2651481772&idx=1&sn=509448890675dbcf03ed1ee877d0bff2&chksm=84ad706fb3daf979f6c5e74e8ec46f09307ffdd358026a33ac98bd13196a79fbabc2db6d746f#rd)
4. [INA226电流计的使用](https://mp.weixin.qq.com/s?__biz=MzA3NzMyNTIyOA==&mid=2651482424&idx=1&sn=5676fb2123294c17a611775965b1f1b1&chksm=84ad7ffbb3daf6eda6cc972bc08e5b0d0781651bada60ca906423fd59090a7f3794fed190d9a#rd)
5. [详解I2C](https://mp.weixin.qq.com/s?__biz=MzA3NzMyNTIyOA==&mid=2651481759&idx=1&sn=562c0748c593e1de21487a538ace637a&chksm=84ad705cb3daf94a2d3eb64d94acc374ea5ff3808b8f5800b4730d9ff02c9a0e1feea61e1566#rd)
6. [python封装动态库](https://mp.weixin.qq.com/s?__biz=MzA3NzMyNTIyOA==&mid=2651481701&idx=1&sn=2ddf1ce70703550bbcaeb7bed4aa0211&chksm=84ad70a6b3daf9b036b859b8b4c621c7a8db6a32ca1e04bd9369b7dc125e17ed16f3ebddc608#rd)
7. [详解SPI](https://mp.weixin.qq.com/s?__biz=MzA3NzMyNTIyOA==&mid=2651481820&idx=2&sn=4d5c44f98a4b174b867b9c05408207d9&chksm=84ad701fb3daf90966a02142c32b14a628b1d8b4564ac448925ccb77796800d6622a071421ee#rd)

## 许可证

本项目使用的许可证在 [`LICENSE`](LICENSE) 文件中给出。

## 贡献

欢迎对本项目做出贡献。在提交[Pull Request](https://github.com/pengwon/ch347-py/pulls)之前，请确保您的代码通过了所有的测试。

## 联系

如果您在使用这个库的过程中遇到任何问题，或者有任何建议和反馈，欢迎通过[GitHub Issues](https://github.com/pengwon/ch347-py/issues)与我们联系。