## Overview
This project is an interactive handheld reaction game built using an ESP32 microcontroller, an OLED display, a rotary encoder, an ADXL345 accelerometer, a NeoPixel LED, and a push button. The goal of the game is to test the player’s reaction speed by presenting quick physical instructions that must be completed within a short time limit. If the player responds correctly within the allowed time, the game continues smoothly. If the player makes a mistake or is too slow, they lose a life. The game ends when all lives are gone and the screen then shows a Game Over menu where the player can choose to play again or exit. This project includes both hardware integration and a custom enclosure design that makes the device easy to use, easy to maintain, and visually clean.

## How the Game Works
When the device is powered on, the OLED begins with a simple start menu. Once the player enters the main game, the screen displays one instruction at a time. These possible instructions include tilting the device left or right as detected through changes in the accelerometer’s X axis, rotating the encoder clockwise or counterclockwise, pressing the encoder’s built-in switch, or pressing the external push button. The player must complete the action before the timer runs out. Feedback is given through both the OLED and the NeoPixel. The screen shows the instruction and the remaining lives, and the NeoPixel provides visual confirmation of success or failure by displaying different colors. The player starts with three lives represented as heart icons at the bottom of the screen. Each failed attempt removes one heart and triggers a brief red flash from the NeoPixel. When the player loses all three lives, the Game Over screen appears. The rotary encoder allows the player to move the cursor between the Play Again and Exit options, and pressing the encoder button confirms the selection.

## Hardware Summary
The ESP32 board serves as the central controller. The OLED display and the ADXL345 accelerometer share the same I2C communication pins. The rotary encoder uses individual digital pins for A, B, and the switch. The NeoPixel receives power from the 3V3 pin and its data signal from a dedicated GPIO pin. An external push button is connected to a separate digital pin and ground. Power is supplied using a LiPo battery connected through a slide switch that allows the device to be turned on and off easily. All components are placed in a compact enclosure that supports quick prototyping and convenient access to the wiring during testing.

## Enclosure Design
The enclosure was designed to be clean, practical, and easy to open. The top cover is printed with transparent PLA so the NeoPixel can shine through the surface without requiring any special window or hole. This gives the device a polished appearance and avoids additional design complexity. The rotary encoder, its push switch, and the external button are mounted through the top panel using their original washers and nuts. I created circular openings that match the diameter of each component so they can be inserted from the front and tightened from the back. This approach keeps the components secure without glue or extra brackets and makes them easy to replace later if needed. To make the enclosure simple to open, I placed small magnets in the corners of both the lid and the base. These magnets allow the top cover to snap into place firmly while still being easy to remove. This makes it convenient to check the wiring, repair parts, or adjust the placement of sensors at any time. The overall design philosophy focuses on usability and maintainability, making sure the enclosure supports frequent testing while keeping the device visually clean.

![Final Product]("C:\Users\WesPu\Desktop\512FPPic.jpg")

## Folder Structure
```
src
code.py       CircuitPython scripts used for the game 

documentation
design     STL file for the enclosure  
System diagram     System structure of this project
Circuit diagram    Draw by KiCAD

README.md  Project overview  
```