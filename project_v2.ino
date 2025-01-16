#include <PubSubClient.h>

#include <WiFi.h>

#include "DHT.h"

#define DHTTYPE DHT11
const char * WIFI_SSID = "Redmi Note 9S"; // Your WiFi SSID
const char * WIFI_PASSWORD = "47472147eadf"; // Your WiFi password
const char * MQTT_SERVER = "34.172.246.156"; // Your VM instance public IP address
const char * MQTT_TOPIC = "iot"; // MQTT topic for subscription
const int MQTT_PORT = 1883; // Non-TLS communication port
const int dht11Pin = 21; // DHT11 sensor pin
const int ledPin = 19;
char buffer[128] = ""; // Text buffer
DHT dht(dht11Pin, DHTTYPE);
WiFiClient espClient;
PubSubClient client(espClient);
void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}
void setup() {
  Serial.begin(9600); // Initiate serial communication
  dht.begin(); // Initialize DHT sensor
  pinMode(19, OUTPUT);
  setup_wifi(); // Connect to the WiFi network
  client.setServer(MQTT_SERVER, MQTT_PORT); // Set up the MQTT client
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  delay(5000);
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  snprintf(buffer, sizeof(buffer), "{\"temperature\": %.2f, \"humidity\": %.2f}", temperature, humidity);
  client.publish(MQTT_TOPIC, buffer);
  Serial.println(buffer);
}

void callback(char* topic, byte* payload, unsigned int length) {
  if(strcmp(topic, "light_switch") == 0) {
    Serial.print("Message arrived [");
    Serial.print(topic);
    Serial.print("] ");
    Serial.println();
    
    // Convert payload to a null-terminated string
    char message[length + 1];
    memcpy(message, payload, length);
    message[length] = '\0'; // Null-terminate the string


    if(strcmp(message, "on") == 0) {
      Serial.println("The light switch is ON");
      digitalWrite(ledPin, HIGH);
    } else if (strcmp(message, "off") == 0) {
      Serial.println("The light switch is OFF");
      digitalWrite(ledPin, LOW);
    } else {
      Serial.print("Unknown payload: ");
      Serial.println(message);
    }

  } else {
    Serial.println("someting went wrong!");
  }
}


void reconnect() {
  while (!client.connected()) {
    Serial.println("Attempting MQTT connection...");
    if (client.connect("ESP32Client")) {
      Serial.println("Connected to MQTT server");
      client.subscribe("light_switch");
    } else {
      Serial.print("Failed, rc=");
      Serial.print(client.state());
      Serial.println(" Retrying in 5 seconds...");
      delay(5000);
    }
  }
}