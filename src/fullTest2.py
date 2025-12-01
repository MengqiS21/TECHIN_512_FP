import time
import board
import busio
import digitalio
import displayio
import terminalio

from adafruit_display_text import label
import adafruit_displayio_ssd1306
import i2cdisplaybus
import adafruit_adxl34x
from neopixel import NeoPixel

# ================================
# I2C: OLED + ADXL345 share D5/D4
# ================================
displayio.release_displays()

i2c = busio.I2C(board.D5, board.D4)  # SCL = D5, SDA = D4

while not i2c.try_lock():
    pass
print("I2C scan:", [hex(x) for x in i2c.scan()])
i2c.unlock()

# ================================
# OLED
# ================================
displayio.release_displays()

display_bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

group = displayio.Group()
line1 = label.Label(terminalio.FONT, text="", anchored_position=(0, 0), anchor_point=(0, 0))
line2 = label.Label(terminalio.FONT, text="", anchored_position=(0, 16), anchor_point=(0, 0))
line3 = label.Label(terminalio.FONT, text="", anchored_position=(0, 32), anchor_point=(0, 0))
group.append(line1)
group.append(line2)
group.append(line3)
display.root_group = group

# ================================
# ADXL345
# ================================
accel = adafruit_adxl34x.ADXL345(i2c)

# ================================
# NeoPixel
# ================================
pixel = NeoPixel(board.D1, 1, auto_write=True)
pixel.brightness = 0.4

def set_pixel_color(r, g, b):
    pixel[0] = (r, g, b)

# ================================
# Rotary Encoder
# A = D0, B = D6, SW = D7
# ================================
clk = digitalio.DigitalInOut(board.D0)   # A
clk.direction = digitalio.Direction.INPUT
clk.pull = digitalio.Pull.UP

dt = digitalio.DigitalInOut(board.D6)    # B
dt.direction = digitalio.Direction.INPUT
dt.pull = digitalio.Pull.UP

enc_sw = digitalio.DigitalInOut(board.D7)  # encoder button
enc_sw.direction = digitalio.Direction.INPUT
enc_sw.pull = digitalio.Pull.UP  # 按下时为 False

last_clk = clk.value
encoder_pos = 0

def update_encoder():
    global last_clk, encoder_pos
    current_clk = clk.value
    if current_clk != last_clk:
        if dt.value != current_clk:
            encoder_pos += 1
        else:
            encoder_pos -= 1
    last_clk = current_clk

def encoder_pressed():
    return not enc_sw.value

# ================================
# push button D8
# ================================
button = digitalio.DigitalInOut(board.D8)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP  # 按下时为 False

def button_pressed():
    return not button.value

# ================================
# Main loop
# ================================
while True:
    update_encoder()

    # update accelerometer
    x, y, z = accel.acceleration

    # read buttons
    btn = button_pressed()
    enc_btn = encoder_pressed()

    # ============ NeoPixel color depends on position ============
    if encoder_pos > 0:
        set_pixel_color(0, 255, 0)      # green
    elif encoder_pos < 0:
        set_pixel_color(255, 0, 0)      # red
    else:
        set_pixel_color(0, 0, 255)      # blue
    # ===============================================================

    # update OLED display
    line1.text = "Enc: {}".format(encoder_pos)
    line2.text = "Btn:{}, EncSW:{}".format(
        "ON" if btn else "OFF",
        "ON" if enc_btn else "OFF"
    )
    line3.text = "Z: {:.2f} m/s^2".format(z)

    time.sleep(0.05)