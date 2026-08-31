#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <ArduinoJson.h>
#include <time.h>

// ==========================================
// اختر البروتوكول هنا: (1 = HTTP, 2 = MQTT)
// ==========================================
#define COMM_PROTOCOL 1

// إعدادات الواي فاي والجهاز
const char* ssid = "aa";
const char* password = "AY470738738";
const char* deviceId = "ESP-01";
const char* encryptionKey = "MY_SECRET_KEY_123";

// إعدادات الخوادم
const char* httpServerUrl = "https://ayham42095hos.pythonanywhere.com/api/data";
const char* mqttServer = "broker.hivemq.com";
const int mqttPort = 1883;
const char* mqttTopic = "iot/anomaly/data";

#define DHTPIN 21
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

// متغيرات عامة
WiFiClient espClient;
WiFiClientSecure secureClient;
PubSubClient mqttClient(espClient);
unsigned long lastTime = 0;
unsigned long timerDelay = 10000; // 10 ثواني افتراضياً

void setup() {
  Serial.begin(9600);
  delay(1000);
  btStop();
  Serial.println("\n=== ESP32 Starting ===");
  
  dht.begin();
  connectToWiFi();
  
  // مزامنة الوقت لحساب التأخير (Latency)
  configTime(3 * 3600, 0, "pool.ntp.org");
  Serial.println("Syncing time...");

  // إعداد MQTT فقط إذا كان الخيار 2 مفعلاً
  #if COMM_PROTOCOL == 2
    mqttClient.setServer(mqttServer, mqttPort);
    mqttClient.setBufferSize(512);
  #endif
}

void connectToWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi Connected! IP: " + WiFi.localIP().toString());
  } else {
    Serial.println("\n❌ WiFi Failed!");
  }
}

void reconnectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Connecting to MQTT...");
    String clientId = "ESP32-" + String(random(0xffff), HEX);
    if (mqttClient.connect(clientId.c_str())) {
      Serial.println("✅ MQTT Connected!");
    } else {
      Serial.print("failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" retrying in 3s");
      delay(3000);
    }
  }
}

void loop() {
  // الحفاظ على اتصال MQTT حياً إذا كان مفعلاً
  #if COMM_PROTOCOL == 2
    if (WiFi.status() == WL_CONNECTED) {
      if (!mqttClient.connected()) {
        reconnectMQTT();
      }
      mqttClient.loop();
    }
  #endif

  if (WiFi.status() == WL_CONNECTED && (millis() - lastTime) >= timerDelay) {
    float h = dht.readHumidity();
    float t = dht.readTemperature();

    if (isnan(h) || isnan(t)) {
      Serial.println("Failed to read DHT!");
      lastTime = millis();
      return;
    }

    Serial.printf("Temp: %.1f C | Hum: %.1f %%\n", t, h);

    // الحصول على وقت القراءة بالميلي ثانية
    struct timeval tv;
    gettimeofday(&tv, NULL);
    unsigned long long clientTimeMs = (unsigned long long)(tv.tv_sec) * 1000 + (unsigned long long)(tv.tv_usec) / 1000;

    // إرسال الحرارة
    sendSensorData("temperature", t, clientTimeMs);
    delay(1000);

    // تحديث الوقت لإرسال الرطوبة
    gettimeofday(&tv, NULL);
    clientTimeMs = (unsigned long long)(tv.tv_sec) * 1000 + (unsigned long long)(tv.tv_usec) / 1000;
    
    // إرسال الرطوبة
    sendSensorData("humidity", h, clientTimeMs);

    lastTime = millis();
  }
}

// دالة موحدة لاختيار طريقة الإرسال
void sendSensorData(String sensorType, float value, unsigned long long clientTimeMs) {
  #if COMM_PROTOCOL == 1
    sendViaHTTP(sensorType, value, clientTimeMs, "HTTP");
  #elif COMM_PROTOCOL == 2
    sendViaMQTT(sensorType, value, clientTimeMs, "MQTT");
  #endif
}

// ==========================================
// دالة الإرسال عبر HTTP
// ==========================================
void sendViaHTTP(String sensorType, float value, unsigned long long clientTimeMs, String proto) {
  secureClient.setInsecure();
  HTTPClient http;
  http.begin(secureClient, httpServerUrl);
  http.addHeader("Content-Type", "application/json");
  
  StaticJsonDocument<256> doc;
  doc["device_id"] = deviceId;
  doc["encryption_key"] = encryptionKey;
  doc["sensor_type"] = sensorType;
  doc["value"] = value;
  doc["client_time"] = clientTimeMs;
  doc["protocol"] = proto;
  
  String jsonStr;
  serializeJson(doc, jsonStr);
  
  Serial.print("Sending via HTTP... ");
  
  int httpResponseCode = http.POST(jsonStr);
  if (httpResponseCode > 0) {
    String response = http.getString();
    StaticJsonDocument<256> resDoc;
    deserializeJson(resDoc, response);
    
    int latency = resDoc["latency_ms"] | 0;
    int newInterval = resDoc["new_interval"] | 0;
    
    Serial.printf("Response: %d | Latency: %d ms\n", httpResponseCode, latency);
    
    // التكيف مع مدة الإرسال الجديدة
    if (newInterval > 0 && (newInterval * 1000) != timerDelay) {
      timerDelay = newInterval * 1000;
      Serial.printf("⏱️ Interval updated to %d seconds\n", newInterval);
    }
  } else {
    Serial.printf("Error: %d\n", httpResponseCode);
  }
  http.end();
}

// ==========================================
// دالة الإرسال عبر MQTT
// ==========================================
void sendViaMQTT(String sensorType, float value, unsigned long long clientTimeMs, String proto) {
  StaticJsonDocument<256> doc;
  doc["device_id"] = deviceId;
  doc["encryption_key"] = encryptionKey;
  doc["sensor_type"] = sensorType;
  doc["value"] = value;
  doc["client_time"] = clientTimeMs;
  doc["protocol"] = proto;
  
  String jsonStr;
  serializeJson(doc, jsonStr);
  
  Serial.print("Publishing via MQTT... ");
  
  if (mqttClient.publish(mqttTopic, jsonStr.c_str())) {
    Serial.println("✅ Published");
  } else {
    Serial.println("❌ Failed to publish");
  }
}