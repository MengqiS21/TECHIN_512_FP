import time
import random
import board
import busio
import digitalio
import displayio
import terminalio

from adafruit_display_text import label
import i2cdisplaybus
import adafruit_displayio_ssd1306
import adafruit_adxl34x
from neopixel import NeoPixel


# -----------------------------------
# Create I2C + ADXL345
# -----------------------------------
displayio.release_displays()
i2c = busio.I2C(board.D3, board.D2)  # SCL = D3, SDA = D2
accel = adafruit_adxl34x.ADXL345(i2c)

# -----------------------------------
# EMA
# -----------------------------------
alpha = 0.2
fx, fy, fz = accel.acceleration  #set initial filtered values

# -----------------------------------
# Baseline
# -----------------------------------
print("Hold still… Calibrating baseline...")
time.sleep(1)

bx_values = []
by_values = []
bz_values = []

for _ in range(20):
    x, y, z = accel.acceleration
    bx_values.append(x)
    by_values.append(y)
    bz_values.append(z)
    time.sleep(0.05)

baseline_x = sum(bx_values) / len(bx_values)
baseline_y = sum(by_values) / len(by_values)
baseline_z = sum(bz_values) / len(bz_values)

print("\nCalibration done.")
print("Baseline X={:.2f}, Y={:.2f}, Z={:.2f}".format(baseline_x, baseline_y, baseline_z))
print("\nNow tilt LEFT or RIGHT and observe changes.\n")

# -----------------------------------
# Show tilt changes
# -----------------------------------
while True:
    x, y, z = accel.acceleration

    # EMA
    fx = alpha * x + (1 - alpha) * fx
    fy = alpha * y + (1 - alpha) * fy
    fz = alpha * z + (1 - alpha) * fz

    dx = fx - baseline_x
    dy = fy - baseline_y
    dz = fz - baseline_z

    print("X={:+.2f}  Y={:+.2f}  Z={:+.2f}".format(dx, dy, dz))

    # tilt LEFT / RIGHT now and watch dx/dy changes
    time.sleep(0.1)
