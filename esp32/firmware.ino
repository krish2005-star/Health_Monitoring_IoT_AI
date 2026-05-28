#include <Wire.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "MAX30100_PulseOximeter.h"

const char* SSID       = "YOUR_WIFI_NAME";
const char* PASSWORD   = "YOUR_WIFI_PASSWORD";
const char* SERVER_URL = "https://abc123.ngrok-free.app/vitals";
const char* DEVICE_ID  = "A001";  // change per patient

PulseOximeter pox;
uint32_t lastReport = 0;

void onBeatDetected() {
    Serial.println("Beat detected");
}

void setup() {
    Serial.begin(115200);

    // connect WiFi
    WiFi.begin(SSID, PASSWORD);
    Serial.print("Connecting to WiFi");
    while (WiFi.status() != WL_CONNECTED) {
        delay(500); Serial.print(".");
    }
    Serial.println("\nConnected! IP: " + WiFi.localIP().toString());

    // init sensor
    if (!pox.begin()) {
        Serial.println("MAX30100 init FAILED");
        while(1);
    }
    pox.setIRLedCurrent(MAX30100_LED_CURR_7_6MA);
    pox.setOnBeatDetectedCallback(onBeatDetected);
    Serial.println("Sensor ready");
}

void loop() {
    pox.update();

    if (millis() - lastReport > 1000) {
        float bpm  = pox.getHeartRate();
        float spo2 = pox.getSpO2();

        if (bpm > 0) {
            Serial.printf("BPM: %.1f  SpO2: %.1f%%\n", bpm, spo2);

            if (WiFi.status() == WL_CONNECTED) {
                HTTPClient http;
                http.begin(SERVER_URL);
                http.addHeader("Content-Type", "application/json");

                StaticJsonDocument<128> doc;
                doc["patient_id"] = DEVICE_ID;
                doc["bpm"]        = bpm;
                doc["spo2"]       = spo2;

                String body;
                serializeJson(doc, body);

                int code = http.POST(body);
                Serial.printf("Server response: %d\n", code);
                http.end();
            }
        }
        lastReport = millis();
    }
}