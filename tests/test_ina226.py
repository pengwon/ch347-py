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

from i2c_devices.ina226 import INA226

# Initialize the INA226 sensor
sensor = INA226()


def read_sensor_data():
    return [sensor.get_bus_voltage(), sensor.get_current(), sensor.get_power()]


# Generator function to produce data from the sensor sensor
def generate_sensor_data():
    data_buffer = []
    while True:
        data = read_sensor_data()
        data_buffer.append(data)
        yield data_buffer
        sleep(0.1)


# Create a figure with 6 subplots for accelerometer and gyroscope data
fig, axs = plt.subplots(3, 1, figsize=(8, 12))

# Initialize empty lines for the accelerometer and gyroscope data plots
lines = [axs[i].plot([], [], lw=2)[0] for i in range(3)]

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
    for i in range(3):
        lines[i].set_data(time_steps[start_index:], [data[i] for data in data_buffer[start_index:]])
        axs[i].set_xlim(start_index, start_index + num_display_points - 1)

    # Update the x-axis limits for scrolling effect
    axs[0].set_ylim(0, 10000)
    axs[1].set_ylim(0, 100000)
    axs[2].set_ylim(0, 200)

    return lines


# Create the generator for sensor sensor data
data_generator = generate_sensor_data()

# Create an animation for real-time plotting, update every 100 milliseconds (0.1 seconds)
ani = animation.FuncAnimation(
    fig, update, frames=range(100), init_func=init, blit=True, interval=100
)

# Add labels and title to each subplot
axis_labels = ["Voltage in mV", "Current in uA", "Power in mW"]
for i in range(3):
    axs[i].set_title(f"{axis_labels[i]}")
    axs[i].set_xlabel("Time Steps")
    axs[i].set_ylabel("INA226 Data Value")

plt.tight_layout()
plt.show()
sensor.close()
