from ch347.ch347 import CH347


def test_i2c():
    ch347 = CH347()
    ch347.open_device()
    print(ch347.stream_i2c([i for i in range(100)], 1))


if __name__ == "__main__":
    test_i2c()
