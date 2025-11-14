import cv2
import mediapipe as mp
import requests
import threading
import time
from collections import deque
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ESP32 Configuration
ESP32_IP = "192.168.4.1"
BASE_URL = f"http://{ESP32_IP}"
REQUEST_TIMEOUT = 1.0
MAX_RETRIES = 2

# Initialize MediaPipe Hands with optimized settings
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.6,
    model_complexity=0  # 0 for faster, 1 for more accurate
)
mp_drawing = mp.solutions.drawing_utils

# State management with debouncing
prev_states = {
    "thumb": None,
    "index": None,
    "middle": None,
    "ring": None,
    "pinky": None,
    "all_down": None
}

# Gesture stability tracking (debouncing)
gesture_buffer = {
    "thumb": deque(maxlen=3),
    "index": deque(maxlen=3),
    "middle": deque(maxlen=3),
    "ring": deque(maxlen=3),
    "pinky": deque(maxlen=3)
}

# Connection tracking
esp32_connected = False
last_connection_check = 0
CONNECTION_CHECK_INTERVAL = 5.0

def check_esp32_connection():
    """Check if ESP32 is reachable"""
    global esp32_connected, last_connection_check
    
    current_time = time.time()
    if current_time - last_connection_check < CONNECTION_CHECK_INTERVAL:
        return esp32_connected
    
    last_connection_check = current_time
    try:
        response = requests.get(f"{BASE_URL}/status", timeout=1.0)
        esp32_connected = response.status_code == 200
        if esp32_connected:
            logger.info("ESP32 connection established")
        return esp32_connected
    except:
        if esp32_connected:
            logger.warning("ESP32 connection lost")
        esp32_connected = False
        return False

def send_command(endpoint, retries=MAX_RETRIES):
    """Send HTTP command to ESP32 with retry logic"""
    def send():
        for attempt in range(retries):
            try:
                url = f"{BASE_URL}/led/{endpoint}"
                response = requests.get(url, timeout=REQUEST_TIMEOUT)
                if response.status_code == 200:
                    logger.debug(f"Command sent: {endpoint} - {response.text}")
                    return
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout sending {endpoint} (attempt {attempt + 1}/{retries})")
            except requests.exceptions.ConnectionError:
                logger.error(f"Connection error for {endpoint}")
                break
            except Exception as e:
                logger.error(f"Error sending {endpoint}: {e}")
                break
            time.sleep(0.1)
    
    threading.Thread(target=send, daemon=True).start()

def get_stable_gesture(finger, current_state):
    """Apply debouncing to gesture detection"""
    gesture_buffer[finger].append(current_state)
    if len(gesture_buffer[finger]) == gesture_buffer[finger].maxlen:
        # All values must agree for stable gesture
        if all(gesture_buffer[finger]) or not any(gesture_buffer[finger]):
            return gesture_buffer[finger][-1]
    return prev_states.get(finger)

def detect_finger_states(hand_landmarks):
    """Detect finger up/down states with improved accuracy"""
    # Get landmarks
    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
    thumb_ip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_IP]
    thumb_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_MCP]
    
    index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    index_pip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_PIP]
    
    middle_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
    middle_pip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_PIP]
    
    ring_tip = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP]
    ring_pip = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_PIP]
    
    pinky_tip = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP]
    pinky_pip = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_PIP]
    
    wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
    
    # Detect hand orientation (left/right)
    hand_is_right = thumb_tip.x < thumb_mcp.x
    
    # Thumb detection (horizontal movement)
    if hand_is_right:
        thumb_up = thumb_tip.x < thumb_ip.x
    else:
        thumb_up = thumb_tip.x > thumb_ip.x
    
    # Other fingers (vertical movement with margin)
    margin = 0.02
    index_up = index_tip.y < (index_pip.y - margin)
    middle_up = middle_tip.y < (middle_pip.y - margin)
    ring_up = ring_tip.y < (ring_pip.y - margin)
    pinky_up = pinky_tip.y < (pinky_pip.y - margin)
    
    return {
        "thumb": thumb_up,
        "index": index_up,
        "middle": middle_up,
        "ring": ring_up,
        "pinky": pinky_up
    }

def process_gestures(hand_landmarks):
    """Process hand gestures and send commands"""
    global prev_states
    
    if not esp32_connected:
        return
    
    # Detect current finger states
    current_states = detect_finger_states(hand_landmarks)
    
    # Apply debouncing for stability
    stable_states = {}
    for finger in ["thumb", "index", "middle", "ring", "pinky"]:
        stable_states[finger] = get_stable_gesture(finger, current_states[finger])
    
    # Check for all fingers down
    all_down = not any(stable_states.values())
    
    # Send commands only on state changes
    if stable_states["thumb"] != prev_states["thumb"] and stable_states["thumb"] is not None:
        send_command("thumb/on" if stable_states["thumb"] else "thumb/off")
    
    if stable_states["index"] != prev_states["index"] and stable_states["index"] is not None:
        send_command("index/on" if stable_states["index"] else "index/off")
    
    if stable_states["middle"] != prev_states["middle"] and stable_states["middle"] is not None:
        send_command("middle/on" if stable_states["middle"] else "middle/off")
    
    if stable_states["ring"] != prev_states["ring"] and stable_states["ring"] is not None:
        send_command("ring/on" if stable_states["ring"] else "ring/off")
    
    if stable_states["pinky"] != prev_states["pinky"] and stable_states["pinky"] is not None:
        send_command("pinky/on" if stable_states["pinky"] else "pinky/off")
    
    if all_down and not prev_states.get("all_down", False):
        send_command("all/off")
        logger.info("All fingers down - all LEDs OFF")
    
    # Update previous states
    prev_states = stable_states.copy()
    prev_states["all_down"] = all_down
    
    return stable_states

def draw_info(frame, finger_states, fps):
    """Draw information overlay on frame"""
    height, width = frame.shape[:2]
    
    # Connection status
    status_text = "ESP32: CONNECTED" if esp32_connected else "ESP32: DISCONNECTED"
    status_color = (0, 255, 0) if esp32_connected else (0, 0, 255)
    cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
    
    # FPS
    cv2.putText(frame, f"FPS: {fps:.1f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # Finger states
    if finger_states:
        y_offset = 100
        for finger, state in finger_states.items():
            if finger != "all_down":
                text = f"{finger.capitalize()}: {'UP' if state else 'DOWN'}"
                color = (0, 255, 0) if state else (100, 100, 100)
                cv2.putText(frame, text, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                y_offset += 25
    
    # Instructions
    cv2.putText(frame, "Press ESC to exit", (10, height - 20), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

def main():
    """Main application loop"""
    global esp32_connected
    
    logger.info("Starting Hand Gesture Recognition System")
    logger.info(f"ESP32 IP: {ESP32_IP}")
    
    # Check ESP32 connection
    check_esp32_connection()
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        logger.error("Failed to open camera")
        return
    
    # Set camera properties for better performance
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    logger.info("Camera initialized successfully")
    
    # FPS calculation
    fps_start_time = time.time()
    fps_frame_count = 0
    current_fps = 0
    
    frame_count = 0
    finger_states = None
    
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                logger.error("Failed to read frame")
                break
            
            # Mirror frame for intuitive interaction
            frame = cv2.flip(frame, 1)
            
            # Convert to RGB for MediaPipe
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process every frame for smooth detection
            frame_count += 1
            
            # Hand detection and tracking
            results = hands.process(frame_rgb)
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Draw hand landmarks
                    mp_drawing.draw_landmarks(
                        frame, 
                        hand_landmarks, 
                        mp_hands.HAND_CONNECTIONS,
                        mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                        mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=2)
                    )
                    
                    # Process gestures
                    finger_states = process_gestures(hand_landmarks)
            
            # Check connection periodically
            if frame_count % 150 == 0:  # Every 5 seconds at 30fps
                check_esp32_connection()
            
            # Calculate FPS
            fps_frame_count += 1
            if time.time() - fps_start_time >= 1.0:
                current_fps = fps_frame_count / (time.time() - fps_start_time)
                fps_frame_count = 0
                fps_start_time = time.time()
            
            # Draw information overlay
            draw_info(frame, finger_states, current_fps)
            
            # Display frame
            cv2.imshow('Hand Gesture Recognition - ESP32 Control', frame)
            
            # Exit on ESC key
            if cv2.waitKey(1) & 0xFF == 27:
                logger.info("ESC pressed - exiting")
                break
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    
    finally:
        # Cleanup
        logger.info("Cleaning up resources")
        cap.release()
        cv2.destroyAllWindows()
        hands.close()
        logger.info("Application closed")

if __name__ == "__main__":
    main()
