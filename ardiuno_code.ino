#include <WiFi.h>
#include <WebServer.h>

// AP Configuration
const char* ssid = "ESP32_GestureControl";
const char* password = "gesture123";

// Web server on port 80
WebServer server(80);

// LED Pin Definitions
struct LEDPin {
  int pin;
  bool state;
  const char* name;
};

LEDPin leds[] = {
  {27, false, "Thumb"},
  {26, false, "Index"},
  {25, false, "Middle"},
  {33, false, "Ring"},
  {32, false, "Pinky"}
};

const int NUM_LEDS = 5;

// Built-in LED for status indication
const int STATUS_LED = 2;

// Timing variables
unsigned long lastClientTime = 0;
unsigned long lastBlinkTime = 0;
bool statusLedState = false;

// Function prototypes
void setupWiFi();
void setupPins();
void setupRoutes();
void handleRoot();
void handleStatus();
void handleLEDControl(int ledIndex, bool state);
void handleAllOff();
void handleAllOn();
void handleNotFound();
void blinkStatusLED();
String getStatusJSON();

void setup() {
  Serial.begin(115200);
  delay(100);
  
  Serial.println("\n\n=================================");
  Serial.println("ESP32 Gesture Control System");
  Serial.println("=================================\n");
  
  setupPins();
  setupWiFi();
  setupRoutes();
  
  Serial.println("\n✓ System Ready");
  Serial.println("=================================\n");
}

void setupPins() {
  Serial.println("Initializing GPIO pins...");
  
  // Initialize LED pins
  for (int i = 0; i < NUM_LEDS; i++) {
    pinMode(leds[i].pin, OUTPUT);
    digitalWrite(leds[i].pin, LOW);
    leds[i].state = false;
    Serial.printf("  - %s LED: GPIO %d\n", leds[i].name, leds[i].pin);
  }
  
  // Initialize status LED
  pinMode(STATUS_LED, OUTPUT);
  digitalWrite(STATUS_LED, LOW);
  
  Serial.println("✓ GPIO pins initialized");
}

void setupWiFi() {
  Serial.println("\nConfiguring Access Point...");
  Serial.printf("  SSID: %s\n", ssid);
  Serial.printf("  Password: %s\n", password);
  
  // Configure AP with specific settings
  WiFi.mode(WIFI_AP);
  WiFi.softAP(ssid, password, 1, 0, 4); // channel 1, not hidden, max 4 clients
  
  delay(500);
  
  IPAddress IP = WiFi.softAPIP();
  Serial.println("\n✓ Access Point Started");
  Serial.print("  IP Address: ");
  Serial.println(IP);
  Serial.println("  Connect your computer to the AP and use this IP in Python script");
}

void setupRoutes() {
  Serial.println("\nSetting up HTTP routes...");
  
  // Root endpoint
  server.on("/", HTTP_GET, handleRoot);
  
  // Status endpoint
  server.on("/status", HTTP_GET, handleStatus);
  
  // Individual LED control
  server.on("/led/thumb/on", HTTP_GET, []() { handleLEDControl(0, true); });
  server.on("/led/thumb/off", HTTP_GET, []() { handleLEDControl(0, false); });
  
  server.on("/led/index/on", HTTP_GET, []() { handleLEDControl(1, true); });
  server.on("/led/index/off", HTTP_GET, []() { handleLEDControl(1, false); });
  
  server.on("/led/middle/on", HTTP_GET, []() { handleLEDControl(2, true); });
  server.on("/led/middle/off", HTTP_GET, []() { handleLEDControl(2, false); });
  
  server.on("/led/ring/on", HTTP_GET, []() { handleLEDControl(3, true); });
  server.on("/led/ring/off", HTTP_GET, []() { handleLEDControl(3, false); });
  
  server.on("/led/pinky/on", HTTP_GET, []() { handleLEDControl(4, true); });
  server.on("/led/pinky/off", HTTP_GET, []() { handleLEDControl(4, false); });
  
  // All LEDs control
  server.on("/led/all/off", HTTP_GET, handleAllOff);
  server.on("/led/all/on", HTTP_GET, handleAllOn);
  
  // 404 handler
  server.onNotFound(handleNotFound);
  
  server.begin();
  Serial.println("✓ HTTP server started");
  Serial.println("\nAvailable endpoints:");
  Serial.println("  GET /");
  Serial.println("  GET /status");
  Serial.println("  GET /led/{thumb|index|middle|ring|pinky}/{on|off}");
  Serial.println("  GET /led/all/{on|off}");
}

void handleRoot() {
  String html = "<!DOCTYPE html><html><head>";
  html += "<meta charset='UTF-8'>";
  html += "<meta name='viewport' content='width=device-width, initial-scale=1.0'>";
  html += "<title>ESP32 Gesture Control</title>";
  html += "<style>";
  html += "body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; background: #f0f0f0; }";
  html += "h1 { color: #333; text-align: center; }";
  html += ".status { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }";
  html += ".led { display: flex; justify-content: space-between; align-items: center; padding: 10px; margin: 10px 0; background: #f9f9f9; border-radius: 5px; }";
  html += ".led-on { background: #4CAF50; color: white; }";
  html += ".led-off { background: #f44336; color: white; }";
  html += ".badge { padding: 5px 15px; border-radius: 20px; font-weight: bold; }";
  html += "button { padding: 10px 20px; margin: 5px; border: none; border-radius: 5px; cursor: pointer; background: #2196F3; color: white; }";
  html += "button:hover { background: #0b7dda; }";
  html += "</style></head><body>";
  
  html += "<h1>🖐️ ESP32 Gesture Control</h1>";
  html += "<div class='status'>";
  html += "<h2>LED Status</h2>";
  
  for (int i = 0; i < NUM_LEDS; i++) {
    html += "<div class='led'>";
    html += "<span><strong>" + String(leds[i].name) + " LED</strong></span>";
    html += "<span class='badge " + String(leds[i].state ? "led-on'>ON" : "led-off'>OFF") + "</span>";
    html += "</div>";
  }
  
  html += "<div style='text-align: center; margin-top: 20px;'>";
  html += "<button onclick=\"fetch('/led/all/on')\">All ON</button>";
  html += "<button onclick=\"fetch('/led/all/off')\">All OFF</button>";
  html += "<button onclick=\"location.reload()\">Refresh</button>";
  html += "</div>";
  html += "</div>";
  html += "<p style='text-align: center; color: #666; margin-top: 20px;'>Connect Python script to control via gestures</p>";
  html += "</body></html>";
  
  server.send(200, "text/html", html);
  Serial.println("[HTTP] Root page served");
}

void handleStatus() {
  String json = getStatusJSON();
  server.send(200, "application/json", json);
  lastClientTime = millis();
}

void handleLEDControl(int ledIndex, bool state) {
  if (ledIndex < 0 || ledIndex >= NUM_LEDS) {
    server.send(400, "text/plain", "Invalid LED index");
    return;
  }
  
  digitalWrite(leds[ledIndex].pin, state ? HIGH : LOW);
  leds[ledIndex].state = state;
  
  String response = String(leds[ledIndex].name) + " LED is " + (state ? "ON" : "OFF");
  server.send(200, "text/plain", response);
  
  Serial.printf("[LED] %s: %s (GPIO %d)\n", leds[ledIndex].name, state ? "ON" : "OFF", leds[ledIndex].pin);
  
  lastClientTime = millis();
}

void handleAllOff() {
  for (int i = 0; i < NUM_LEDS; i++) {
    digitalWrite(leds[i].pin, LOW);
    leds[i].state = false;
  }
  server.send(200, "text/plain", "All LEDs OFF");
  Serial.println("[LED] All LEDs turned OFF");
  lastClientTime = millis();
}

void handleAllOn() {
  for (int i = 0; i < NUM_LEDS; i++) {
    digitalWrite(leds[i].pin, HIGH);
    leds[i].state = true;
  }
  server.send(200, "text/plain", "All LEDs ON");
  Serial.println("[LED] All LEDs turned ON");
  lastClientTime = millis();
}

void handleNotFound() {
  String message = "404: Endpoint Not Found\n\n";
  message += "URI: " + server.uri() + "\n";
  message += "Method: " + String((server.method() == HTTP_GET) ? "GET" : "POST") + "\n";
  server.send(404, "text/plain", message);
  Serial.printf("[HTTP] 404 - %s\n", server.uri().c_str());
}

String getStatusJSON() {
  String json = "{";
  json += "\"connected\":true,";
  json += "\"uptime\":" + String(millis()) + ",";
  json += "\"leds\":{";
  
  for (int i = 0; i < NUM_LEDS; i++) {
    json += "\"" + String(leds[i].name) + "\":" + String(leds[i].state ? "true" : "false");
    if (i < NUM_LEDS - 1) json += ",";
  }
  
  json += "}}";
  return json;
}

void blinkStatusLED() {
  unsigned long currentTime = millis();
  
  // Blink pattern based on client activity
  unsigned long timeSinceClient = currentTime - lastClientTime;
  
  if (timeSinceClient < 100) {
    // Fast blink when receiving commands
    if (currentTime - lastBlinkTime >= 100) {
      statusLedState = !statusLedState;
      digitalWrite(STATUS_LED, statusLedState);
      lastBlinkTime = currentTime;
    }
  } else if (timeSinceClient < 5000) {
    // Slow blink when recently active
    if (currentTime - lastBlinkTime >= 500) {
      statusLedState = !statusLedState;
      digitalWrite(STATUS_LED, statusLedState);
      lastBlinkTime = currentTime;
    }
  } else {
    // Solid on when idle
    digitalWrite(STATUS_LED, HIGH);
  }
}

void loop() {
  server.handleClient();
  blinkStatusLED();
  
  // Optional: Add periodic status updates
  static unsigned long lastPrint = 0;
  if (millis() - lastPrint >= 30000) { // Every 30 seconds
    Serial.printf("\n[Status] Uptime: %lu ms | Clients: %d\n", 
                  millis(), WiFi.softAPgetStationNum());
    lastPrint = millis();
  }
}
