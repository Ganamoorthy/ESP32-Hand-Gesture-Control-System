# ESP32-Hand-Gesture-Control-System
Real-time hand gesture control of ESP32 LEDs using Python and MediaPipe. Detects individual finger states with debouncing for stability, sending Wi-Fi HTTP commands to toggle LEDs via an ESP32 web server. A modular, edge AI system ideal for learning embedded networking, computer vision, and IoT control.

# ESP32 Hand Gesture Control System
Control ESP32 GPIOs using real-time hand gesture recognition with Python, OpenCV, and MediaPipe.

# Features

  * Real-time five-finger detection and debounced gesture recognition
 
  * Wireless communication from Python to ESP32 via HTTP (Wi-Fi AP mode)
 
  * Visual feedback: LED status and robust HTML dashboard
 
  * Modular, extensible codebase (easy to add new devices/actuators)
 
  * No external cloud dependency: fast local control

# System Architecture

| Component      | Description                                                   |
| -------------- | ------------------------------------------------------------- |
| Python Client  | Detects hand gestures, sends HTTP commands via threading      |
| ESP32 Firmware | Web server processes REST requests to control GPIO LEDs       |
| Communication  | Wi-Fi AP direct connection (default SSIDESP32_GestureControl) |

# Quickstart
1. Upload Arduino code to ESP32

    * Edit Wi-Fi SSID/password in setupWiFi() if needed.
      
2. Run Python script

   * Ensure OpenCV, MediaPipe, and requests are installed
     
     (pip install opencv-python mediapipe requests).

   * Connect to ESP32 AP and start camera:
     
             python gesture.py
     
3. Test gestures

   * Each finger’s up/down status toggles individual LEDs in real time.

# Code Overview
 * gesture.py handles OpenCV video, finger detection, connection checks, and non-blocking ESP32 requests.

 * ESP32 Arduino code hosts the web server and manages LED GPIOs by endpoint.

# Customization
 * Replace LEDs in leds[] with relays, motors, or other actuators.

 * Adjust gesture logic for more complex control signals.

# License
This project is open source, intended for learning and non-commercial use.
Please respect copyrights of all libraries.
