#include <Arduino.h>

#include <ESP8266WiFi.h>
#include <ESP8266WiFiMulti.h>

#include <ArduinoJson.h>
#include <SocketIOclient.h>
// #include <SocketIoClient.h>
#include <vector>
#include <string.h>
#include <Hash.h>

ESP8266WiFiMulti WiFiMulti;
SocketIOclient socketIO;
// SocketIoClient socketIO;

#define USE_SERIAL Serial

const char *SSID = "21-5F";
const char *password = "0912459717";
const char *server = "192.168.1.106";
const int server_port = 3000;
const unsigned long resendTime = 1000;

char *UID = "uiduid";
bool registered = false;

const std::vector<std::string> split(const std::string &str, const std::string&pattern);

void socketIOEvent(socketIOmessageType_t type, uint8_t * payload, size_t length) {
    std::vector<std::string> splitInfo;
    switch(type) {
        case sIOtype_DISCONNECT:
            USE_SERIAL.printf("[IOc] Disconnected!\n");
            break;
        case sIOtype_CONNECT:
            USE_SERIAL.printf("[IOc] Connected to url: %s\n", payload);
            
            // join default namespace (no auto join in Socket.IO V3)
            socketIO.send(sIOtype_CONNECT, "/");
            break;
        case sIOtype_EVENT:
            splitInfo = split(std::string((char *)payload), "\"");
            if (splitInfo[1] == "registerInfo"){
              if (String(UID) == String("uiduid")){
                strcpy(UID, splitInfo[3].c_str());
                registered = true;
              }
            }
            // USE_SERIAL.printf("[IOc] get event: %s\n", payload);
            USE_SERIAL.printf("[IOc] get event: %s, message: %s\n", splitInfo[1].c_str(), splitInfo[3].c_str());
            USE_SERIAL.flush();
            break;
        case sIOtype_ACK:
            USE_SERIAL.printf("[IOc] get ack: %u\n", length);
            hexdump(payload, length);
            break;
        case sIOtype_ERROR:
            USE_SERIAL.printf("[IOc] get error: %u\n", length);
            hexdump(payload, length);
            break;
        case sIOtype_BINARY_EVENT:
            USE_SERIAL.printf("[IOc] get binary: %u\n", length);
            hexdump(payload, length);
            break;
        case sIOtype_BINARY_ACK:
            USE_SERIAL.printf("[IOc] get binary ack: %u\n", length);
            hexdump(payload, length);
            break;
    }
}

void setup() {
    USE_SERIAL.begin(115200);

    //Serial.setDebugOutput(true);
    USE_SERIAL.setDebugOutput(true);
    USE_SERIAL.setTimeout(1);

    WiFi.mode(WIFI_STA);
    WiFiMulti.addAP(SSID, password);

    //WiFi.disconnect();
    while(WiFiMulti.run() != WL_CONNECTED) {
        delay(100);
    }

    String ip = WiFi.localIP().toString();
    USE_SERIAL.printf("[SETUP] WiFi Connected %s\n", ip.c_str());

    // server address, port, URL and protocol
    
    socketIO.begin(server, server_port, "/socket.io/?EIO=4");//"/socket.io/?EIO=4"
    socketIO.onEvent(socketIOEvent);
    String reginfo = "\[\"registerInfo\"]";
    socketIO.sendEVENT(reginfo);
}

unsigned long ts1, ts2, ts3;
unsigned long sendTime = millis();
int registerSend = 0;
int maxSendRegister = 2;
void loop() {
    socketIO.loop(); 

    if((registerSend < maxSendRegister) && (millis() - sendTime > resendTime)) {
        String reg = "\[\"signalRegister\",\"\"]";
        socketIO.sendEVENT(reg);
        sendTime = millis();
        registerSend++;
        if (String(UID) != "uiduid"){
            registerSend += maxSendRegister;
        }
    }
    if(registered && USE_SERIAL.available()){
        ts1 = micros();
        String rcv = USE_SERIAL.readString();
        ts1 = micros() - ts1;
        if (rcv.indexOf('\r') != -1){
            // creat JSON message for Socket.IO (event)
            ts2 = micros();
            DynamicJsonDocument doc(64);
            JsonArray array = doc.to<JsonArray>();

            // add evnet name
            // Hint: socket.on('event_name', ....
            array.add(UID);
            array.add(rcv.substring(0, rcv.indexOf('\r')));
            ts2 = micros() - ts2;

            // add payload (parameters) for the event
            // JsonObject param1 = array.createNestedObject();
            // param1["data"] = snd;

            // JSON to String (serializion)
            ts3 = micros();
            String output;
            serializeJson(doc, output);

            // Send event
            socketIO.sendEVENT(output);
            ts3 = micros() - ts3;

            // Print JSON for debugging
            USE_SERIAL.print(ts1);
            USE_SERIAL.print(",");
            USE_SERIAL.print(ts2);
            USE_SERIAL.print(",");
            USE_SERIAL.println(ts3);
            // USE_SERIAL.print(",");
            // USE_SERIAL.println(output);
        }
    }
}

const std::vector<std::string> split(const std::string &str, const std::string &pattern) {
    std::vector<std::string> result;
    std::string::size_type begin, end;

    end = str.find(pattern);
    begin = 0;

    while (end != std::string::npos) {
        if (end - begin != 0) {
            result.push_back(str.substr(begin, end-begin)); 
        }    
        begin = end + pattern.size();
        end = str.find(pattern, begin);
    }

    if (begin != str.length()) {
        result.push_back(str.substr(begin));
    }
    return result;        
}
