import requests

# ESP32 IP (default for AP mode)
ESP32_IP = "192.168.4.1"

# Test function to turn thumb LED ON
def test_led():
    try:
        url = f"http://{ESP32_IP}/led/thumb/off"
        response = requests.get(url, timeout=2)  # 2-second timeout
        print(f"Response from ESP32: {response.text}")
    except Exception as e:
        print(f"Failed to send command: {e}")

if __name__ == "__main__":
    test_led()
