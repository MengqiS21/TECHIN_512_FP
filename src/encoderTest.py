import time
import board
import digitalio

# ---------------------------
# Rotary Encoder Pins
# ---------------------------
pinA = digitalio.DigitalInOut(board.D0)
pinA.direction = digitalio.Direction.INPUT
pinA.pull = digitalio.Pull.UP

pinB = digitalio.DigitalInOut(board.D6)
pinB.direction = digitalio.Direction.INPUT
pinB.pull = digitalio.Pull.UP

# Button SW
sw = digitalio.DigitalInOut(board.D7)
sw.direction = digitalio.Direction.INPUT
sw.pull = digitalio.Pull.UP  # HIGH = released, LOW = pressed

# ---------------------------
# Encoder state
# ---------------------------

def read_state():
    """Read encoder AB pins as a 2-bit state: 0..3"""
    a = 1 if pinA.value else 0
    b = 1 if pinB.value else 0
    # You can swap a/b order if your wiring is reversed
    return (a << 1) | b   # state: 0b00, 0b01, 0b10, 0b11

# Transition table for a standard 2-bit quadrature encoder.
# Keys: previous_state -> {current_state: "CW"/"CCW"}
transition_table = {
    0b00: {0b01: "CW",  0b10: "CCW"},
    0b01: {0b11: "CW",  0b00: "CCW"},
    0b11: {0b10: "CW",  0b01: "CCW"},
    0b10: {0b00: "CW",  0b11: "CCW"},
}

last_state = read_state()

# Accumulate steps to filter noise
cw_steps = 0
ccw_steps = 0
STEPS_PER_CLICK = 2     # Require 2 valid transitions to print once

last_sw = sw.value

print("State-machine encoder test running...")

while True:
    # ---------------------------
    # Rotation using state machine
    # ---------------------------
    current_state = read_state()

    if current_state != last_state:
        # Tiny delay to help mechanical bounce settle
        time.sleep(0.001)

        # Re-read to confirm stable state
        stable_state = read_state()

        if stable_state != last_state:
            # Look up direction from transition table
            dir_map = transition_table.get(last_state, {})
            direction = dir_map.get(stable_state, None)

            if direction == "CW":
                cw_steps += 1
                ccw_steps = 0      # reset opposite direction (noise)
            elif direction == "CCW":
                ccw_steps += 1
                cw_steps = 0       # reset opposite direction (noise)
            else:
                # Invalid jump (noise), reset both
                cw_steps = 0
                ccw_steps = 0

            # When enough consistent steps accumulated, print once
            if cw_steps >= STEPS_PER_CLICK:
                print("Rotated: CW (state-machine)")
                cw_steps = 0
            if ccw_steps >= STEPS_PER_CLICK:
                print("Rotated: CCW (state-machine)")
                ccw_steps = 0

            last_state = stable_state

    # ---------------------------
    # Button click detection
    # ---------------------------
    current_sw = sw.value
    if last_sw and not current_sw:   # released -> pressed
        print("Button pressed!")
        time.sleep(0.15)            # debounce
    last_sw = current_sw

    time.sleep(0.001)  # loop pacing