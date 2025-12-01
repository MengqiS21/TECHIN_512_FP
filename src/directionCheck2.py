import time
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

# =========================
#  Hardware setup
# =========================

# --- I2C: OLED + ADXL345 共用 D5/D4 ---
displayio.release_displays()
i2c = busio.I2C(board.D5, board.D4)  # SCL=D5, SDA=D4

# --- OLED 128x64 ---
display_bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

main_group = displayio.Group()
line1 = label.Label(terminalio.FONT, text="", anchor_point=(0, 0),
                    anchored_position=(0, 0))
line2 = label.Label(terminalio.FONT, text="", anchor_point=(0, 0),
                    anchored_position=(0, 16))
line3 = label.Label(terminalio.FONT, text="", anchor_point=(0, 0),
                    anchored_position=(0, 32))
main_group.append(line1)
main_group.append(line2)
main_group.append(line3)
display.root_group = main_group

# --- ADXL345 (share i2c)) ---
accel = adafruit_adxl34x.ADXL345(i2c)

# --- NeoPixel: D1 ---
pixel = NeoPixel(board.D1, 1, auto_write=True)
pixel.brightness = 0.3

def set_color(r, g, b):
    pixel[0] = (r, g, b)

# =========================
#  Calibration
# =========================

line1.text = "TILT TEST"
line2.text = "Hold device still"
line3.text = "Calibrating..."
set_color(0, 0, 50) 

time.sleep(1.0)

samples = 40
sx = sy = sz = 0.0
for _ in range(samples):
    x, y, z = accel.acceleration
    sx += x
    sy += y
    sz += z
    time.sleep(0.02)

base_x = sx / samples
base_y = sy / samples
base_z = sz / samples

line1.text = "Calibrated!"
line2.text = "BaseX:{:.2f}".format(base_x)
line3.text = "BaseY:{:.2f}".format(base_y)
set_color(0, 50, 0) 
time.sleep(1.5)

# =========================
#  Test
# =========================

TILT_TH = 2.0  

while True:
    x, y, z = accel.acceleration
    dx = x - base_x
    dy = y - base_y

    # OLED show change difference
    # X  row
    line1.text = "X:{:+5.2f} dX:{:+5.2f}".format(x, dx)
    # Y  row
    line2.text = "Y:{:+5.2f} dY:{:+5.2f}".format(y, dy)
    # Z row
    line3.text = "Z:{:+5.2f}".format(z)

    # NeoPixel color indication (only check X tilt)
    if dx > TILT_TH:
        # Tilted RIGHT
        set_color(0, 255, 0) 
    elif dx < -TILT_TH:
        # Tilted LEFT
        set_color(255, 0, 0)
    else:
        # baseline
        set_color(0, 0, 80)  # 蓝色

    time.sleep(0.05)