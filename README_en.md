# ch347-py

[中文](README.md)

## Introduction

`ch347-py` is a Python binding library for driving the CH347 chip. It provides a simple way to interact with the CH347 chip, and can be used to develop applications for I2C, SPI, and other communication interfaces.

## Installation

### Using pip

You can install this library using pip:

```bash
pip install ch347-py
```

### From Source

Using uv for development (recommended):

```bash
git clone https://github.com/pengwon/ch347-py.git
cd ch347-py

# Install uv (if not already installed)
pip install uv

# Create virtual environment and install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows
```

Using traditional method:

```bash
git clone https://github.com/pengwon/ch347-py.git
cd ch347-py
pip install -e .
```

### Development Setup

If you want to contribute to development or run tests, install development dependencies:

```bash
# Using uv (recommended)
uv sync

# or using pip
pip install -e ".[dev]"
```

## Usage

First, you need to import the `CH347` class from the `ch347` module:

```python
from ch347 import CH347
```

Then, you can create an instance of the `CH347` class and use its methods to interact with the CH347 chip. For example:

```python
driver = CH347()
driver.spi_write(0x00, [0xFF] * 10)
```

## Testing

This project includes some test scripts. You can run these scripts to test and demonstrate how to use this library.

## References

1. [Reading and displaying data from the MPU6050 sensor](https://mp.weixin.qq.com/s?__biz=MzA3NzMyNTIyOA==&mid=2651481825&idx=1&sn=bbe2833173dcf0420eaac9faff14ca8b&chksm=84ad7022b3daf9349f8e57e87abacef833bd742f655a60379e07e8ee2529cb012d807a132a92#rd)
2. [Reading and writing SPI Flash](https://mp.weixin.qq.com/s?__biz=MzA3NzMyNTIyOA==&mid=2651481820&idx=1&sn=b28a3b59fa7104383ced33ddf9cee7c5&chksm=84ad701fb3daf9099a0245f143c6fc3f5398af3657cf028e052fa3ad944aa510730fee319fa8#rd)
3. [Connecting MPU6050](https://mp.weixin.qq.com/s?__biz=MzA3NzMyNTIyOA==&mid=2651481772&idx=1&sn=509448890675dbcf03ed1ee877d0bff2&chksm=84ad706fb3daf979f6c5e74e8ec46f09307ffdd358026a33ac98bd13196a79fbabc2db6d746f#rd)
4. [Using the INA226 ammeter](https://mp.weixin.qq.com/s?__biz=MzA3NzMyNTIyOA==&mid=2651482424&idx=1&sn=5676fb2123294c17a611775965b1f1b1&chksm=84ad7ffbb3daf6eda6cc972bc08e5b0d0781651bada60ca906423fd59090a7f3794fed190d9a#rd)
5. [Detailed explanation of I2C](https://mp.weixin.qq.com/s?__biz=MzA3NzMyNTIyOA==&mid=2651481759&idx=1&sn=562c0748c593e1de21487a538ace637a&chksm=84ad705cb3daf94a2d3eb64d94acc374ea5ff3808b8f5800b4730d9ff02c9a0e1feea61e1566#rd)
6. [Python encapsulation of dynamic libraries](https://mp.weixin.qq.com/s?__biz=MzA3NzMyNTIyOA==&mid=2651481701&idx=1&sn=2ddf1ce70703550bbcaeb7bed4aa0211&chksm=84ad70a6b3daf9b036b859b8b4c621c7a8db6a32ca1e04bd9369b7dc125e17ed16f3ebddc608#rd)
7. [Detailed explanation of SPI](https://mp.weixin.qq.com/s?__biz=MzA3NzMyNTIyOA==&mid=2651481820&idx=2&sn=4d5c44f98a4b174b867b9c05408207d9&chksm=84ad701fb3daf90966a02142c32b14a628b1d8b4564ac448925ccb77796800d6622a071421ee#rd)

## License

The license used by this project is given in the [`LICENSE`](LICENSE) file.

## Contributions

Contributions to this project are welcome. Before submitting a [Pull Request](https://github.com/pengwon/ch347-py/pulls), please make sure your code passes all tests.

## Contact

If you encounter any problems while using this library, or have any suggestions and feedback, please contact us through [GitHub Issues](https://github.com/pengwon/ch347-py/issues).