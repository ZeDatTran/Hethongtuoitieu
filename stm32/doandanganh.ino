#include <WiFi.h>
#include <Adafruit_MQTT.h>
#include <Adafruit_MQTT_Client.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <DHT.h>
#include <TimeLib.h>
#include <NTPClient.h>
#include <WiFiUdp.h>

LiquidCrystal_I2C lcd(0x27, 16, 2);
const char* ssid = "abcd";
const char* password = "12345678";
#define AIO_SERVER "io.adafruit.com"
#define AIO_SERVERPORT 1883
#define AIO_USERNAME "dadanganh"
#define AIO_KEY "aio_MprK98xPGjMIUXq8zI9HXJh5g44X"
#define DHTPIN 4
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "pool.ntp.org", 0, 60000);
#define soil 32
#define RELAY_PIN_1 18
#define PUSH_BUTTON_1 19

WiFiClient client;
Adafruit_MQTT_Client mqtt(&client, AIO_SERVER, AIO_SERVERPORT, AIO_USERNAME, AIO_KEY);

// Feeds
Adafruit_MQTT_Publish temperatureFeed = Adafruit_MQTT_Publish(&mqtt, AIO_USERNAME "/feeds/temperature");
Adafruit_MQTT_Publish humidityFeed = Adafruit_MQTT_Publish(&mqtt, AIO_USERNAME "/feeds/humidity");
Adafruit_MQTT_Publish soilMoistureFeed = Adafruit_MQTT_Publish(&mqtt, AIO_USERNAME "/feeds/soilmoisture");
Adafruit_MQTT_Publish relayFeed = Adafruit_MQTT_Publish(&mqtt, AIO_USERNAME "/feeds/relaycontrol");
Adafruit_MQTT_Subscribe relayControl = Adafruit_MQTT_Subscribe(&mqtt, AIO_USERNAME "/feeds/relaycontrol");
Adafruit_MQTT_Subscribe soilTargetFeed = Adafruit_MQTT_Subscribe(&mqtt, AIO_USERNAME "/feeds/soilmoisturetarget");
Adafruit_MQTT_Subscribe autoEnableFeed = Adafruit_MQTT_Subscribe(&mqtt, AIO_USERNAME "/feeds/autoenable");

int relay1State = LOW;
int previousRelayState = LOW;
bool pumpState = false;
bool isTimerEnable = false;
bool autoEnable = false;
int soilMin = 40;  // Giá trị mặc định
int soilMax = 60;  // Giá trị mặc định

unsigned long previousDataSendMillis = 0;
const long dataSendInterval = 30000;
unsigned long previousLCDUpdateMillis = 0;
const long lcdUpdateInterval = 1000;
unsigned long previousRelaySendMillis = 0;
const long relaySendCooldown = 1000;

// Callback cho relaycontrol
void relayCallback(char *data, uint16_t len) {
  String message = String(data);
  Serial.print("Received from relaycontrol: ");
  Serial.println(message);
  
  if (message == "ON") {
    relay1State = HIGH;
  } else if (message == "OFF") {
    relay1State = LOW;
  }
  digitalWrite(RELAY_PIN_1, relay1State);
  updateLCDForRelay();
  
  unsigned long currentMillis = millis();
  if (currentMillis - previousRelaySendMillis >= relaySendCooldown) {
    MQTT_connect();
    relayFeed.publish(relay1State == HIGH ? "ON" : "OFF");
    previousRelaySendMillis = currentMillis;
  }
}

// Callback cho soilmoisturetarget (min-max)
void soilTargetCallback(char *data, uint16_t len) {
  String message = String(data);
  Serial.print("Received soil moisture target: ");
  Serial.println(message);

  // Phân tích min và max từ chuỗi "min-max"
  int separatorIndex = message.indexOf('-');
  if (separatorIndex != -1) {
    soilMin = message.substring(0, separatorIndex).toInt();
    soilMax = message.substring(separatorIndex + 1).toInt();
    Serial.printf("Min: %d, Max: %d\n", soilMin, soilMax);
  }
}

// Callback cho autoenable (switch)
void autoEnableCallback(char *data, uint16_t len) {
  String message = String(data);
  autoEnable = (message == "ON");
  Serial.print("Auto mode: ");
  Serial.println(autoEnable ? "Enabled" : "Disabled");
}

void initializeLCD() {
  lcd.clear();
}

void updateLCDForRelay() {
  if (relay1State == HIGH) {
    lcd.setCursor(11, 1);
    lcd.print("W:ON ");
  } else {
    lcd.setCursor(11, 1);
    lcd.print("W:OFF");
  }
}

void DHT11sensor() {
  float h = dht.readHumidity();
  float t = dht.readTemperature();
  if (isnan(h) || isnan(t)) {
    Serial.println("Failed to read from DHT sensor!");
    return;
  }
  lcd.setCursor(0, 0);
  lcd.print("T:");
  lcd.print(t, 1);
  lcd.setCursor(8, 0);
  lcd.print("H:");
  lcd.print(h, 1);
  Serial.print("Temperature: ");
  Serial.print(t);
  Serial.print(" °C, Humidity: ");
  Serial.print(h);
  Serial.println(" %");
}

void soilMoistureSensor() {
  int value = analogRead(soil);
  value = map(value, 0, 4095, 0, 100);
  value = (value - 100) * -1;
  lcd.setCursor(0, 1);
  lcd.print("S:");
  lcd.print(value);
  lcd.print(" ");
  
  if (autoEnable) {
    unsigned long currentMillis = millis();
    if (value < soilMin && relay1State == LOW) {
      relay1State = HIGH;
      digitalWrite(RELAY_PIN_1, relay1State);
      if (currentMillis - previousRelaySendMillis >= relaySendCooldown) {
        MQTT_connect();
        relayFeed.publish("ON");
        previousRelaySendMillis = currentMillis;
      }
      lcd.setCursor(11, 1);
      lcd.print("W:ON ");
    } else if (value >= soilMax && relay1State == HIGH) {
      relay1State = LOW;
      digitalWrite(RELAY_PIN_1, relay1State);
      if (currentMillis - previousRelaySendMillis >= relaySendCooldown) {
        MQTT_connect();
        relayFeed.publish("OFF");
        previousRelaySendMillis = currentMillis;
      }
      lcd.setCursor(11, 1);
      lcd.print("W:OFF");
    }
  }
}

void updateLCDForAuto() {
  lcd.setCursor(5, 1);
  lcd.print("A:");
  lcd.print(autoEnable ? "ON " : "OFF");
}

void sendSensorData() {
  float h = dht.readHumidity();
  float t = dht.readTemperature();
  int soilValue = analogRead(soil);
  soilValue = map(soilValue, 0, 4095, 0, 100);
  soilValue = (soilValue - 100) * -1;
  
  MQTT_connect();
  temperatureFeed.publish(t);
  humidityFeed.publish(h);
  soilMoistureFeed.publish((int32_t)soilValue);
  Serial.println("Data sent to Adafruit IO:");
  Serial.print("Temperature: ");
  Serial.print(t);
  Serial.print(" °C, Humidity: ");
  Serial.print(h);
  Serial.print(" %, Soil Moisture: ");
  Serial.print(soilValue);
  Serial.println(" %");
}

void checkPhysicalButton() {
  if (digitalRead(PUSH_BUTTON_1) == LOW) {
    delay(200); // Debounce
    relay1State = !relay1State;
    digitalWrite(RELAY_PIN_1, relay1State);
    
    unsigned long currentMillis = millis();
    if (currentMillis - previousRelaySendMillis >= relaySendCooldown) {
      MQTT_connect();
      relayFeed.publish(relay1State == HIGH ? "ON" : "OFF");
      previousRelaySendMillis = currentMillis;
      Serial.println(relay1State == HIGH ? "p: ON" : "p: OFF");
    }
    while (digitalRead(PUSH_BUTTON_1) == LOW);
    delay(200); // Debounce
  }
}

void setup() {
  Serial.begin(9600);
  Wire.begin();
  lcd.init();
  lcd.backlight();
  pinMode(RELAY_PIN_1, OUTPUT);
  pinMode(PUSH_BUTTON_1, INPUT_PULLUP);
  
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");

  dht.begin();
  timeClient.begin();
  initializeLCD();

  // Subscribe các feed
  mqtt.subscribe(&relayControl);
  relayControl.setCallback(relayCallback);
  mqtt.subscribe(&soilTargetFeed);
  soilTargetFeed.setCallback(soilTargetCallback);
  mqtt.subscribe(&autoEnableFeed);
  autoEnableFeed.setCallback(autoEnableCallback);
  
  MQTT_connect();
}

void loop() {
  MQTT_connect();
  unsigned long currentMillis = millis();

  if (currentMillis - previousDataSendMillis >= dataSendInterval) {
    previousDataSendMillis = currentMillis;
    sendSensorData();
  }

  if (currentMillis - previousLCDUpdateMillis >= lcdUpdateInterval) {
    previousLCDUpdateMillis = currentMillis;
    DHT11sensor();
    soilMoistureSensor();
    updateLCDForAuto();
  }

  if (relay1State != previousRelayState) {
    previousRelayState = relay1State;
    initializeLCD();
    updateLCDForRelay();
  }

  updateLCDForRelay();
  checkPhysicalButton();

  mqtt.processPackets(100);
}

void MQTT_connect() {
  int8_t ret;
  if (mqtt.connected()) {
    return;
  }
  Serial.print("Connecting to Adafruit IO...");
  uint8_t retries = 3;
  while ((ret = mqtt.connect()) != 0) {
    Serial.println(mqtt.connectErrorString(ret));
    Serial.println("Retrying Adafruit IO connection in 5 seconds...");
    mqtt.disconnect();
    delay(5000);
    retries--;
    if (retries == 0) {
      while (1);
    }
  }
  Serial.println("Adafruit IO connected!");
}