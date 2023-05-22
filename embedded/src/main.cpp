#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include "env.h"

#define lightsw 23
#define fansw 22
#define distsens 3
#define oneWireBus 4

OneWire oneWire(oneWireBus);
DallasTemperaturesensors(&oneWire);


void setup() {
  // put your setup code here, to run once:
  pinMode(lightsw,OUTPUT);
  pinMode(fansw,OUTPUT);
  pinMode(distsens,INPUT);
  //pinMode(oneWireBus,INPUT);
  // WiFi_SSID and WIFI_PASS should be stored in the env.h
  WiFi.begin(WIFI_SSID, WIFI_PASS,6);

	// Connect to wifi
  Serial.println("Connecting");
  while(WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.print("Connected to WiFi network with IP Address: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  // put your main code here, to run repeatedly:
  if(WiFi.status()== WL_CONNECTED){

    HTTPClient http;
  
    // Establish a connection to the server
    http.begin(API_URL);
    
    // Specify content-type header
    //for(int i=0; i<8; i++){
      

      http.addHeader("Content-Type", "application/json");
      //http.addHeader("X-API-Key", API_KEY);
      //http.addHeader("Content-length", "76");

      // Serialise JSON object into a string to be sent to the API
      StaticJsonDocument<1000> doc;
      String httpRequestData;
      
        //switchonoff(i);
      sensors.requestTemperatures();

      Serial.print("Temperature: ");
      Serial.println(sensors.getTempCByIndex(0));

      Serial.print("Distance: ");
      Serial.println(digitalRead(distsens));

        doc["temperature"] = sensors.getTempCByIndex(0);
        doc["presence"] = digitalRead(distsens);
        //doc["light_switch_3"] = ledonoff[i][2];
  
      serializeJson(doc, httpRequestData);


      // Send HTTP POST request
      int httpResponseCode = http.PUT(httpRequestData);
      String http_response;

      // check result of POST request. negative response code means server wasn't reached
     
   
      Serial.print("HTTP Response code: ");
      Serial.println(httpResponseCode);

      http_response = http.getString();
      Serial.println(http_response);
      
      // Free resources
      http.end();

      delay(2000);

    //  }
    //GET
    HTTPclient http;
    String http_response;

    http.begin(API_URL);

    int httpResponseCode = http.GET();

    if (httpResponseCode>0){
        Serial.print("HTTP Response Code: ");
        Serial.println(httpResponseCode);

        Serial.print("Response from server: ");
        http_response = http.getString();
        Serial.print(http_response);
    }
  else{
        Serial.print("Error code: ");
        Serial.println(httpResponseCode);
    //return;
  }
   http.end();

  StaticJsonDocument<1000> doc;

  DeserializationError error = deserializeJson(doc, http_response);
  if (error){
    Serial.print("deserializeJson() failed: ");
    Serial.println(error.c_str());
    return;
      }

      bool fanswt =doc["fan"];
      bool lightswt =doc["light"];
      //digitalWrite(fanswitch,temperature);
      //digitalWrite(lightswitch,light);
      Serial.println("");

      Serial.print("light_switch:");
      Serial.println(lightsw);
      Serial.print("fan Switch:");
      Serial.println(fansw);

      Serial.println("");

      digitalWrite(fansw,fanswt);
      digitalWrite(lightsw,lightswt);
      //http.end();
      }

  else {
    
        Serial.print("Error: ");
        //Serial.println(httpResponseCode);
    //return;
    Serial.println("WiFi Disconnected");
  }

}
