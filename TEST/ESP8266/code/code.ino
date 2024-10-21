#include <ESP8266WiFi.h>
#include <ESP8266mDNS.h>
#include <DHT.h>

// DHT sensor settings
#define DHTPIN D5     // D5 is GPIO14 on ESP8266
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

// Wi-Fi settings
const char* ssid = "Hawaii";         // Replace with your Wi-Fi SSID
const char* password = "12345678Aa"; // Replace with your Wi-Fi password

// Server settings
const char* server_hostname = "raspberrypi.local"; // Replace with your Raspberry Pi's hostname followed by .local
const char* server_ip="192.168.0.100";
const uint16_t server_port = 8888;                 // Server port as specified in your code

// Room ID (you can change this to any identifier you prefer)
const char* room_id = "1";

void setup() {
  // Initialize serial communication for debugging
  Serial.begin(115200);
  delay(10);

  // Initialize DHT sensor
  dht.begin();

  // Connect to Wi-Fi network
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  // Wait for connection
  int wifi_retry_count = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    wifi_retry_count++;
    if (wifi_retry_count > 60) { // Wait for 30 seconds max
      Serial.println("Failed to connect to Wi-Fi");
      return;
    }
  }

  Serial.println();
  Serial.println("Wi-Fi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  // Start mDNS
  if (MDNS.begin("esp8266")) {
    Serial.println("MDNS responder started");
  } else {
    Serial.println("Error setting up MDNS responder!");
  }
}

void loop() {
  // Wait a few seconds between measurements
  delay(2000);

  // Reading temperature and humidity
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature(); // Read temperature as Celsius

  // Check if any reads failed
  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("Failed to read from DHT sensor!");
    return;
  }

  // Prepare data string in the format: room_id temperature humidity
  String data = String(room_id) + " " + String(temperature) + " " + String(humidity);
  Serial.print("Data to send: ");
  Serial.println(data);

  // Resolve the server hostname to an IP address
  IPAddress server_ip;
  if (!WiFi.hostByName(server_hostname, server_ip)) {
    Serial.println("Failed to resolve server hostname");
    return;
  }

  // Connect to the server
  WiFiClient client;
  if (!client.connect(server_ip, server_port)) {
    Serial.println("Connection to server failed");
    return;
  }

  // Send data to the server
  client.println(data);
  Serial.println("Data sent to server");

  // Close the connection
  client.stop();

  // Wait before next reading (e.g., 60 seconds)
  delay(60000);
}
