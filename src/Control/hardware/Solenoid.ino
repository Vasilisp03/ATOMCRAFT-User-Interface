#include <WiFiS3.h>
#include <WiFiUdp.h>
#include <PID_v1.h>

int status = WL_IDLE_STATUS;
char ssid[] = "Optus_540FC8";        // your network SSID (name)
char pass[] = "lased29799mq";    // your network password (use for WPA, or use as key for WEP)
int keyIndex = 0;

unsigned int localPort = 2390;      // local port to listen on
char packetBuffer[256]; //buffer to hold incoming packet
bool manualMode = false;
unsigned long manualEndTime = 0;
WiFiUDP Udp;

const int pressureSensorPin = 1;
const int solenoidPin = 4;
int lengthMS = 2000;

double setpoint = 110;
double input, output;

double Kp = 2.0, Ki = 5.0, Kd = 1.9;
PID myPid(&input, &output, &setpoint, Kp, Ki, Kd, DIRECT);

void setup() {
  Serial.begin(9600);
  while (!Serial);

  pinMode(solenoidPin, OUTPUT);
  digitalWrite(solenoidPin, HIGH); // Solenoid valve starts closed
  pinMode(pressureSensorPin, INPUT);

  if (WiFi.status() == WL_NO_MODULE) {
    Serial.println("Communication with WiFi module failed!");
    while (true);
  }

  String fv = WiFi.firmwareVersion();
  if (fv < WIFI_FIRMWARE_LATEST_VERSION) {
    Serial.println("Please upgrade the firmware");
  }

  while (status != WL_CONNECTED) {
    Serial.print("Attempting to connect to SSID: ");
    Serial.println(ssid);
    status = WiFi.begin(ssid, pass);
    delay(10000);
  }
  Serial.println("Connected to WiFi");
  printWifiStatus();

  Udp.begin(localPort);
  myPid.SetMode(AUTOMATIC);
  myPid.SetOutputLimits(0, 1);

  Serial.println("Ready to receive input");
}

void loop() {
  int packetSize = Udp.parsePacket();
  if (packetSize) {
    int len = Udp.read(packetBuffer, 255);
    if (len > 0) {
      packetBuffer[len] = 0;
    }

    Serial.print("Received: ");
    Serial.println(packetBuffer);

    packetBuffer[strcspn(packetBuffer, "\r\n")] = 0;

    // Read Pressure Sensor
    input = readPressure();
    Serial.print("Pressure reading: ");
    Serial.println(input);

    myPid.Compute();

    digitalWrite(solenoidPin, output > 0.5 ? LOW : HIGH);
    Serial.println(output > 0.5 ? "Solenoid OPEN" : "Solenoid CLOSED");

    // Send pressure and status data back to PC
    String dataPacket = String(input) + "," + (output > 0.5 ? "OPEN" : "CLOSED");
    Udp.beginPacket("192.168.1.100", 2391); // Send to PC receiver port
    Udp.print(dataPacket);
    Udp.endPacket();

    // Handle commands
    if (strcmp(packetBuffer, "o") == 0) {
      Serial.println("Opening solenoid valve");
      digitalWrite(solenoidPin, LOW);
      delay(lengthMS);
      digitalWrite(solenoidPin, HIGH);
      Serial.println("Solenoid closed");
      Serial.println("Executing code within if statement");
    
    } else if (strcmp(packetBuffer, "pressure") == 0) {
      // Send current pressure reading
      Serial.print("Pressure request - current reading: ");
      Serial.println(input);
      
    } else {
      int newLength = atoi(packetBuffer);
      if (newLength > 0) {
        lengthMS = newLength;
        Serial.print("Updated solenoid open time to: ");
        Serial.print(lengthMS);
        Serial.println(" ms");

      } else {
        Serial.println("Invalid time received!");
      } 
    } 

    Udp.beginPacket(Udp.remoteIP(), Udp.remotePort());
    Udp.write("ack");
    Udp.endPacket();
  }
}

double readPressure()
 {
  return digitalRead(pressureSensorPin) ? 120 : 80;
 }
void printWifiStatus() {
  Serial.print("SSID: ");
  Serial.println(WiFi.SSID());
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
  Serial.print("signal strength (RSSI):");
  Serial.print(WiFi.RSSI());
  Serial.println(" dBm");
}