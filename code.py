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

# =========================
#  Hardware setup
# =========================

# --- Display (OLED 128x64, I2C D5/D4) ---
displayio.release_displays()
i2c = busio.I2C(board.D5, board.D4)  # SCL=D5, SDA=D4

display_bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

main_group = displayio.Group()

line1 = label.Label(terminalio.FONT, text="", anchor_point=(0, 0),
                    anchored_position=(0, 0))
line2 = label.Label(terminalio.FONT, text="", anchor_point=(0, 0),
                    anchored_position=(0, 16))
line3 = label.Label(terminalio.FONT, text="", anchor_point=(0, 0),
                    anchored_position=(0, 32))
# 新增：最底下一行专门显示 LIVES: ***
line_lives = label.Label(terminalio.FONT, text="", anchor_point=(0, 0),
                         anchored_position=(0, 48))

main_group.append(line1)
main_group.append(line2)
main_group.append(line3)
main_group.append(line_lives)  # 把 lives 行加进显示组
display.root_group = main_group

def show_text(l1="", l2="", l3=""):
    """Show up to 3 lines of text on the OLED (menus, opening)."""
    line1.text = l1
    line2.text = l2
    line3.text = l3
    # 菜单 / 开机画面不显示 LIVES
    line_lives.text = ""

# --- Accelerometer ADXL345 (same I2C on D5/D4) ---
i2c_accel = i2c
accel = adafruit_adxl34x.ADXL345(i2c_accel)

# --- Rotary Encoder: A=D0, B=D6, SW=D7 ---
clk = digitalio.DigitalInOut(board.D0)
clk.direction = digitalio.Direction.INPUT
clk.pull = digitalio.Pull.UP

dt = digitalio.DigitalInOut(board.D6)
dt.direction = digitalio.Direction.INPUT
dt.pull = digitalio.Pull.UP

enc_sw = digitalio.DigitalInOut(board.D7)
enc_sw.direction = digitalio.Direction.INPUT
enc_sw.pull = digitalio.Pull.UP  # pressed -> False

# Encoder button state for "click" event detection
last_enc_sw = enc_sw.value  # True = released, False = pressed

# --- Push Button: D8 ---
button = digitalio.DigitalInOut(board.D8)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP  # pressed -> False

# Push button state for "click" event detection
last_button_state = button.value  # True = released, False = pressed

# --- NeoPixel: D1, 1 LED ---
pixel = NeoPixel(board.D1, 1, auto_write=True)
pixel.brightness = 0.3

# =========================
#  Helper: NeoPixel colors
# =========================

def set_color(r, g, b):
    """Set NeoPixel to a solid color."""
    pixel[0] = (r, g, b)

def flash_color(r, g, b, t=0.15):
    """Flash NeoPixel with a color for a short time and restore previous color."""
    old = pixel[0]
    pixel[0] = (r, g, b)
    time.sleep(t)
    pixel[0] = old

# =========================
#  Encoder: button click
# =========================

def encoder_clicked():
    """
    Detect a single 'click' event of the encoder button.
    We treat a transition from released -> pressed as one click.
    """
    global last_enc_sw
    current = enc_sw.value
    clicked = False
    # released (True) -> pressed (False)
    if last_enc_sw and (not current):
        clicked = True
    last_enc_sw = current
    return clicked

# =========================
#  Encoder: state-machine for rotation
# =========================

def read_encoder_state():
    """Read encoder AB pins as a 2-bit state: value 0..3."""
    a = 1 if clk.value else 0
    b = 1 if dt.value else 0
    # (a << 1) | b gives: 0b00, 0b01, 0b10, 0b11
    return (a << 1) | b

# Transition table for a standard quadrature encoder.
# Keys: previous_state -> {current_state: "CW"/"CCW"}
transition_table = {
    0b00: {0b01: "CW",  0b10: "CCW"},
    0b01: {0b11: "CW",  0b00: "CCW"},
    0b11: {0b10: "CW",  0b01: "CCW"},
    0b10: {0b00: "CW",  0b11: "CCW"},
}

last_enc_state = read_encoder_state()
cw_steps = 0
ccw_steps = 0
STEPS_PER_TURN = 2   # require 2 valid transitions before we accept a turn

def encoder_reset_turns():
    """Reset accumulated CW/CCW steps before waiting for a new rotation move."""
    global cw_steps, ccw_steps
    cw_steps = 0
    ccw_steps = 0

def encoder_read_turn():
    """
    Check encoder rotation using the state machine.
    Returns:
        "CW"  - when a stable clockwise turn is detected,
        "CCW" - when a stable counter-clockwise turn is detected,
        None  - if no full turn is detected this call.
    """
    global last_enc_state, cw_steps, ccw_steps

    current_state = read_encoder_state()

    if current_state != last_enc_state:
        # Small delay to reduce mechanical bounce
        time.sleep(0.001)
        stable_state = read_encoder_state()

        if stable_state != last_enc_state:
            dir_map = transition_table.get(last_enc_state, {})
            direction = dir_map.get(stable_state, None)

            if direction == "CW":
                cw_steps += 1
                ccw_steps = 0  # reset opposite direction
            elif direction == "CCW":
                ccw_steps += 1
                cw_steps = 0
            else:
                # Invalid jump / noise
                cw_steps = 0
                ccw_steps = 0

            last_enc_state = stable_state

            if cw_steps >= STEPS_PER_TURN:
                cw_steps = 0
                ccw_steps = 0
                return "CW"
            if ccw_steps >= STEPS_PER_TURN:
                cw_steps = 0
                ccw_steps = 0
                return "CCW"

    return None

# =========================
#  Button reading
# =========================

def button_clicked():
    """
    Detect a single 'click' event of the separate push button (D8).
    We treat a transition from released -> pressed as one click.
    """
    global last_button_state
    current = button.value
    clicked = False
    # released (True) -> pressed (False)
    if last_button_state and (not current):
        clicked = True
    last_button_state = current
    return clicked

def button_pressed():
    """Return True while the separate push button (D8) is pressed."""
    return not button.value

# =========================
#  Accelerometer calibration / filtering
# =========================

alpha = 0.2  # low-pass filter factor
fx, fy, fz = accel.acceleration  # initial read

accel_baseline = [0.0, 0.0, 0.0]
accel_filtered = [fx, fy, fz]

def calibrate_accel(samples=30):
    """Take samples and compute baseline for x, y, z when the device is held still."""
    global accel_baseline, accel_filtered
    sx = sy = sz = 0.0
    for _ in range(samples):
        x, y, z = accel.acceleration
        sx += x
        sy += y
        sz += z
        time.sleep(0.02)
    baseline_x = sx / samples
    baseline_y = sy / samples
    baseline_z = sz / samples
    accel_baseline = [baseline_x, baseline_y, baseline_z]
    accel_filtered[:] = accel_baseline[:]  # initialize filter with baseline

def read_filtered_accel():
    """Read acceleration and apply a simple low-pass filter."""
    global accel_filtered
    x, y, z = accel.acceleration
    fx = alpha * x + (1 - alpha) * accel_filtered[0]
    fy = alpha * y + (1 - alpha) * accel_filtered[1]
    fz = alpha * z + (1 - alpha) * accel_filtered[2]
    accel_filtered = [fx, fy, fz]
    return accel_filtered

# =========================
#  Moves & difficulty
# =========================

MOVES = [
    "TURN_CW",
    "TURN_CCW",
    "PUSH_BTN",
    "PUSH_ENC",
    "TILT_LEFT",
    "TILT_RIGHT",
]

# Retro-style labels for each move
MOVE_LABELS = {
    "TURN_CW":    "TURN RIGHT >>",
    "TURN_CCW":   "<< TURN LEFT",
    "PUSH_BTN":   "PUSH BUTTON",
    "PUSH_ENC":   "PRESS KNOB",
    "TILT_LEFT":  "TILT LEFT <",
    "TILT_RIGHT": "TILT RIGHT >",
}

DIFFICULTIES = ["EASY", "MED", "HARD"]
DIFF_TIMES = {   # base time limit per move
    "EASY": 3.0,
    "MED": 2.0,
    "HARD": 1.2,
}

def difficulty_label(diff):
    """Return a user-friendly difficulty label."""
    if diff == "EASY":
        return "EASY"
    if diff == "MED":
        return "MEDIUM"
    if diff == "HARD":
        return "HARD"
    return diff

# =========================
#  Lives / hearts
# =========================

MAX_LIVES = 3
lives = MAX_LIVES  # will be reset at the start of each game

def hearts_string():
    """
    Build a lives string based on current lives.
    Use only ASCII so it always shows on terminalio font.
    Example: 'LIVES: ***' when lives == 3.
    """
    return "LIVES: " + ("*" * lives)

def show_game_text(l1="", l2=""):
    """
    Show two lines of game text, with current lives on the bottom line.
    Lives are shown at the very bottom of the screen (y = 48).
    """
    line1.text = l1
    line2.text = l2
    line3.text = ""           # 游戏时不再使用中间这行
    line_lives.text = hearts_string()

# =========================
#  Difficulty selection (menu using encoder_read_turn)
# =========================

def choose_difficulty():
    """
    Use the encoder to select game difficulty.
    Turn to change difficulty, press knob to confirm.
    Uses encoder_read_turn() so it shares the same stable encoder logic as the game.
    """
    options = DIFFICULTIES
    current_index = 0  # 0=EASY, 1=MED, 2=HARD

    show_text("SELECT MODE",
              "> " + difficulty_label(options[current_index]),
              "")
    set_color(0, 0, 50)

    while True:
        # Read encoder rotation using state-machine
        turn = encoder_read_turn()
        if turn == "CW":
            if current_index < len(options) - 1:
                current_index += 1
                show_text(
                    "SELECT MODE",
                    "> " + difficulty_label(options[current_index]),
                    ""
                )
        elif turn == "CCW":
            if current_index > 0:
                current_index -= 1
                show_text(
                    "SELECT MODE",
                    "> " + difficulty_label(options[current_index]),
                    ""
                )

        # Encoder button click to confirm
        if encoder_clicked():
            flash_color(0, 255, 0, 0.2)
            return options[current_index]

        time.sleep(0.005)

# =========================
#  Wait for a specific move
# =========================

def wait_for_move(expected_move, time_limit):
    """
    Wait for the player to perform the expected move within time_limit seconds.
    Uses:
      - encoder_read_turn() for TURN_CW / TURN_CCW
      - encoder_clicked() for PUSH_ENC
      - button_clicked() for PUSH_BTN (edge-based click)
      - filtered accelerometer for TILT_LEFT / TILT_RIGHT
    Returns True if done in time, False otherwise.
    """
    start_time = time.monotonic()

    set_color(80, 80, 0)  # yellow: waiting

    # Tilt detection based on X axis:
    # left tilt  = X becomes larger than baseline
    # right tilt = X becomes smaller than baseline
    TILT_TH = 2.0  # threshold, can be tuned by feel

    # Reset encoder turn accumulation before waiting
    encoder_reset_turns()

    while time.monotonic() - start_time < time_limit:
        fx, fy, fz = read_filtered_accel()

        # Push button (D8): trigger as soon as it is pressed (level-based)
        if expected_move == "PUSH_BTN" and button_pressed():
            flash_color(0, 255, 0)
            # Wait for release so it does not auto-trigger the next move
            while button_pressed():
                time.sleep(0.01)
            return True


        # Encoder button click (press the knob)
        if expected_move == "PUSH_ENC" and encoder_clicked():
            flash_color(0, 255, 0)
            return True

        # Rotation moves via state-machine
        turn_dir = encoder_read_turn()
        if expected_move == "TURN_CW" and turn_dir == "CW":
            flash_color(0, 255, 0)
            return True
        if expected_move == "TURN_CCW" and turn_dir == "CCW":
            flash_color(0, 255, 0)
            return True

        # Tilt moves based on X axis
        dx = fx - accel_baseline[0]

        # Left tilt: X increases enough
        if expected_move == "TILT_LEFT" and dx > TILT_TH:
            flash_color(0, 255, 0)
            return True

        # Right tilt: X decreases enough
        if expected_move == "TILT_RIGHT" and dx < -TILT_TH:
            flash_color(0, 255, 0)
            return True

        time.sleep(0.01)

    # Overtime = failure
    set_color(255, 0, 0)
    return False

# =========================
#  Life handling & end states
# =========================

def lose_life(level):
    """
    Reduce one life, flash red, and show a short message.
    Returns True if this hit causes total game over (no lives left),
    otherwise False (player can continue with remaining lives).
    """
    global lives
    lives -= 1
    flash_color(255, 0, 0, 0.3)  # red flash

    if lives > 0:
        show_game_text("OOPS! LIFE -1", "RETRY LEVEL {}".format(level))
        set_color(255, 0, 0)
        time.sleep(1.5)
        return False
    else:
        show_game_text("OUT OF LIVES", "GAME OVER L{}".format(level))
        set_color(255, 0, 0)
        time.sleep(2.0)
        return True

def show_game_win():
    """Show a short win screen (actual replay/exit menu is handled outside)."""
    set_color(0, 255, 0)
    show_game_text("STAGE CLEAR!", "ALL 10 LEVELS")
    time.sleep(2.0)

# =========================
#  Generic menu: PLAY / EXIT (using encoder_read_turn)
# =========================

def menu_play_exit(title_top, play_label="PLAY", exit_label="EXIT"):
    """
    Show a two-option menu controlled by the encoder:
      - Both options are displayed on screen at the same time.
      - A '>' cursor marks the current selection.
      - Rotate encoder to move the cursor between options.
      - Press encoder button to confirm.
    Menus use plain show_text; lives are not shown here.
    """
    options = [play_label, exit_label]
    current_index = 0  # 0 = PLAY, 1 = EXIT

    def draw_menu():
        if current_index == 0:
            line2_text = "> " + options[0]
            line3_text = "  " + options[1]
        else:
            line2_text = "  " + options[0]
            line3_text = "> " + options[1]
        show_text(title_top, line2_text, line3_text)

    draw_menu()
    set_color(0, 0, 50)

    while True:
        # Use the same stable encoder rotation logic
        turn = encoder_read_turn()
        if turn == "CW":
            if current_index < len(options) - 1:
                current_index += 1
                draw_menu()
        elif turn == "CCW":
            if current_index > 0:
                current_index -= 1
                draw_menu()

        # Click to confirm current selection
        if encoder_clicked():
            flash_color(0, 255, 0, 0.2)
            return options[current_index]

        time.sleep(0.005)

# =========================
#  Game loop
# =========================

def play_game():
    """
    Main game logic for one run:
      - Ask for difficulty
      - Calibrate accelerometer
      - Start with 3 lives
      - Up to 10 levels, each level has a longer sequence
      - Mistake => lose one life; only end game when all lives are used
    During the game, every page bottom line shows lives.
    """
    global lives
    lives = MAX_LIVES

    difficulty = choose_difficulty()
    base_time = DIFF_TIMES[difficulty]

    # From here on, use show_game_text so lives appear on every game page
    show_game_text("GET READY!", "MODE: " + difficulty_label(difficulty))
    set_color(0, 0, 80)
    time.sleep(1.5)

    show_game_text("HOLD STILL", "CALIBRATING...")
    calibrate_accel()
    time.sleep(0.5)

    time_limit = base_time
    level = 1

    while level <= 10 and lives > 0:
        sequence_len = level
        sequence = [random.choice(MOVES) for _ in range(sequence_len)]

        show_game_text(
            "LEVEL {}  {}".format(level, difficulty_label(difficulty)),
            "{:d} MOVES, {:.1f}s".format(sequence_len, time_limit)
        )
        set_color(0, 0, 80)
        time.sleep(1.5)

        level_cleared = True

        for index, move in enumerate(sequence):
            label_text = MOVE_LABELS[move]
            show_game_text(
                "L{} {}/{} {}".format(
                    level, index + 1, sequence_len, difficulty_label(difficulty)
                ),
                "DO: " + label_text
            )

            success = wait_for_move(move, time_limit)
            if not success:
                # Player made a mistake on this move
                is_game_over = lose_life(level)
                level_cleared = False
                if is_game_over:
                    # All lives used: end entire game
                    return False  # game ended by failure
                else:
                    # Still has lives: restart this level
                    break

        if level_cleared:
            flash_color(0, 200, 0, 0.3)
            level += 1
            time_limit *= 0.9  # slightly harder each level

    if lives > 0:
        # Player cleared all levels with at least 1 life left
        show_game_win()
        return True
    else:
        return False

# =========================
#  90s arcade-style opening screen
# =========================

def opening_screen():
    """
    Show a 90s arcade-style splash screen for about 5 seconds.
    '>> START FUN <<' is roughly centered by using leading spaces.
    (Opening screen does not show lives.)
    """
    start = time.monotonic()
    while time.monotonic() - start < 5.0:
        # First frame: show text (center-ish)
        show_text("RETRO REACTOR",
                  "   90s ARCADE STYLE",
                  "   >> START FUN <<")
        set_color(0, 0, 80)
        time.sleep(0.7)

        # Second frame: hide bottom line
        show_text("RETRO REACTOR",
                  "   90s ARCADE STYLE",
                  "")
        set_color(0, 0, 20)
        time.sleep(0.3)

# =========================
#  Main loop with opening + menus
# =========================

set_color(0, 0, 50)

while True:
    # Always show opening screen first
    opening_screen()

    # Then enter menu / game loop
    while True:
        # Pre-game menu: choose to PLAY or EXIT
        choice = menu_play_exit("RETRO REACTOR", play_label="PLAY", exit_label="EXIT")
        if choice == "EXIT":
            # Back to opening screen
            break
        else:
            # Start one game run
            result = play_game()  # True = win, False = lose

            # Post-game menu: PLAY AGAIN or EXIT
            if result:
                title = "YOU WIN!"
            else:
                title = "GAME OVER"

            choice_after = menu_play_exit(title, play_label="PLAY AGAIN", exit_label="EXIT")
            if choice_after == "EXIT":
                # Back to opening screen
                break
            # else: loop back to pre-game menu