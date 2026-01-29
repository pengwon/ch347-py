import os
import sys
from time import sleep

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np

# Get the parent directory's path
parent_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Add the parent directory to the system path if not already present
if parent_directory not in sys.path:
    sys.path.insert(0, parent_directory)

from i2c_devices.mpu6050 import MPU6050

# Initialize the MPU6050 sensor
mpu6050 = MPU6050()


# Replace these lines with the actual import and initialization of the MPU6050 sensor
# For demonstration purposes, we use dummy functions to generate random data
def read_mpu6050_accel_data():
    accel_data = mpu6050.get_accel_data(True)
    return [accel_data["x"], accel_data["y"], accel_data["z"]]


def read_mpu6050_gyro_data():
    gyro_data = mpu6050.get_gyro_data()
    return [gyro_data["x"], gyro_data["y"], gyro_data["z"]]


# Generator function to produce data from the MPU6050 sensor
def generate_mpu6050_data():
    data_buffer = []
    while True:
        accel_data = read_mpu6050_accel_data()
        gyro_data = read_mpu6050_gyro_data()
        data_buffer.append(accel_data + gyro_data)
        yield data_buffer
        sleep(0.1)


# Create a figure with 6 subplots for accelerometer and gyroscope data
fig, axs = plt.subplots(6, 1, figsize=(8, 12))

# Initialize empty lines for the accelerometer and gyroscope data plots
lines = [axs[i].plot([], [], lw=2)[0] for i in range(6)]

# Set the number of data points to be displayed on the plot
num_display_points = 50


def init():
    for line in lines:
        line.set_data([], [])
    return lines


def update(frame):
    data_buffer = next(data_generator)

    # Generate the x-axis values (time steps) based on the number of data points
    time_steps = np.arange(len(data_buffer))

    # Get the starting index to display a specific number of data points
    start_index = max(0, len(data_buffer) - num_display_points)

    # Update the plot data for accelerometer and gyroscope
    for i in range(6):
        lines[i].set_data(time_steps[start_index:], [data[i] for data in data_buffer[start_index:]])

        # Adjust the plot limits for better visualization
        if i < 3:
            axs[i].set_ylim(-2, 2)  # Accelerometer data range: -2 to +2
        else:
            axs[i].set_ylim(-200, 200)  # Gyroscope data range: -200 to +200
        axs[i].set_xlim(start_index, start_index + num_display_points - 1)

    return lines


# Create the generator for MPU6050 sensor data
data_generator = generate_mpu6050_data()

# Create an animation for real-time plotting, update every 100 milliseconds (0.1 seconds)
ani = animation.FuncAnimation(
    fig, update, frames=range(100), init_func=init, blit=True, interval=100
)

# Add labels and title to each subplot
axis_labels = ["AX", "AY", "AZ", "GX", "GY", "GZ"]
for i in range(6):
    axs[i].set_title(f"{axis_labels[i]} Data")
    axs[i].set_xlabel("Time Steps")
    axs[i].set_ylabel("MPU6050 Data Value")

plt.tight_layout()
plt.show()
mpu6050.close()
