import os
import sys

import pytest

# Add the parent directory to the path to import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ch347 import CH347


def test_device_information():
    """Test to connect to a device and print its information."""
    # Try to open a device
    try:
        device = CH347()
        device.list_devices()
        assert device is not None, "Failed to create device instance"

        # Open the first available device
        result = device.open_device()
        assert result, "Failed to open device"

        # Get device information
        device_info = device.get_device_info()

        # Close the device
        device.close_device()

    except Exception as e:
        pytest.fail(f"Test failed with exception: {str(e)}")


if __name__ == "__main__":
    # Allow running the test directly
    test_device_information()
