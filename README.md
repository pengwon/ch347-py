# ch347-py

[English](README_en.md)

## 简介

`ch347-py`是一个用于驱动CH347芯片的Python绑定库。它提供了一种简单的方式来与CH347芯片进行交互，可以基于此开发I2C、SPI等通信接口应用。

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