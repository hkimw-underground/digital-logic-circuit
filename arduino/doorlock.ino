#include <SPI.h>
#include <MFRC522.h>
#include <Keypad.h>

// NFC 핀. Uno/Nano 기준 SPI는 11(MOSI), 12(MISO), 13(SCK)을 사용한다.
#define SS_PIN 10
#define RST_PIN A2
MFRC522 mfrc522(SS_PIN, RST_PIN);

// 키패드 설정
const byte ROWS = 4; 
const byte COLS = 4; 
char keys[ROWS][COLS] = {
  {'1','2','3','A'},
  {'4','5','6','B'},
  {'7','8','9','C'},
  {'*','0','#','D'}
};
byte rowPins[ROWS] = {2, 3, 4, 5};
byte colPins[COLS] = {6, 7, 8, A0};
Keypad keypad = Keypad( makeKeymap(keys), rowPins, colPins, ROWS, COLS );

// 릴레이 설정. active-low 모듈이면 RELAY_LOCKED와 RELAY_UNLOCKED를 서로 바꾼다.
const int RELAY_PIN = A1;
const int RELAY_LOCKED = LOW;
const int RELAY_UNLOCKED = HIGH;
const unsigned long DOOR_OPEN_MS = 3000;

String inputPassword = "";
bool doorOpen = false;
unsigned long doorOpenedAt = 0;

void setup() {
  Serial.begin(9600);
  SPI.begin();
  mfrc522.PCD_Init();
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, RELAY_LOCKED);
  Serial.println("SYSTEM_READY");
}

void loop() {
  serviceDoorTimer();
  handleNfc();
  handleKeypad();
  handleServerCommand();
}

void handleNfc() {
  if (mfrc522.PICC_IsNewCardPresent() && mfrc522.PICC_ReadCardSerial()) {
    String uid = "";
    for (byte i = 0; i < mfrc522.uid.size; i++) {
      uid += String(mfrc522.uid.uidByte[i] < 0x10 ? "0" : "");
      uid += String(mfrc522.uid.uidByte[i], HEX);
    }
    uid.toUpperCase();
    Serial.println("WAKEUP:NFC:" + uid);
    mfrc522.PICC_HaltA();
    mfrc522.PCD_StopCrypto1();
  }
}

void handleKeypad() {
  char key = keypad.getKey();
  if (key) {
    if (key == '*') {
      inputPassword = "";
      return;
    }

    if (key == '#') {
      sendPassword();
      return;
    }

    if (inputPassword.length() < 8) {
      inputPassword += key;
    }
    if (inputPassword.length() >= 4) {
      sendPassword();
    }
  }
}

void handleServerCommand() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    if (command == "OPEN_DOOR" || command == "ACTION:OPEN") {
      openDoor();
    }
  }
}

void sendPassword() {
  if (inputPassword.length() == 0) {
    return;
  }
  Serial.println("WAKEUP:PW:" + inputPassword);
  inputPassword = "";
}

void openDoor() {
  digitalWrite(RELAY_PIN, RELAY_UNLOCKED);
  doorOpen = true;
  doorOpenedAt = millis();
  Serial.println("DOOR_OPENED");
}

void serviceDoorTimer() {
  if (doorOpen && millis() - doorOpenedAt >= DOOR_OPEN_MS) {
    digitalWrite(RELAY_PIN, RELAY_LOCKED);
    doorOpen = false;
    Serial.println("DOOR_CLOSED");
  }
}
