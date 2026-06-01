/*
 * doorlock_firmware.ino
 * 2FA 스마트 도어락 — Arduino Uno R4 WiFi
 *
 * USB-C 시리얼을 통해 서버(PC/Raspberry Pi)와 통신한다.
 * NFC + PIN 1차 인증 → 서버 → 얼굴 인식 2차 인증 → 도어 개방
 *
 * 현재 연결: TTP229 터치키패드(SZH-SSBH-065), 부저(FQ-030), 브레드보드
 * 미연결:   NFC, LED, 릴레이 → ACTIVE 플래그 false
 *
 * 배선 기준: pin_connect_set.md
 */

// NFC 사용 시 true로 변경
#define NFC_ACTIVE          false

#if NFC_ACTIVE
#include <SPI.h>
#include <MFRC522.h>
#endif

// ╔══════════════════════════════════════════════════════════╗
// ║  PIN CONFIGURATION — pin_connect_set.md 기준 배선       ║
// ╚══════════════════════════════════════════════════════════╝

// --- NFC (MFRC522 / SZH-EK040) --- 현재 미연결 ----------------------
#if NFC_ACTIVE
#define NFC_SS_PIN    10    // SDA → D10
#define NFC_RST_PIN   9     // RST → D9~
#endif

// --- TTP229 터치 키패드 (SZH-SSBH-065) ----------------------------
// 16키 모드: 모듈의 TP2 패드를 GND에 쇼트해야 16키 활성화
// SDO → D2, SCL → D3 (프로토콜: TTP229 시리얼, I2C 아님)
#define KP_SDO_PIN    2     // SDO (Serial Data Out)
#define KP_SCL_PIN    3     // SCL (Serial Clock)

// 키패드 매핑: TTP229의 키 1~16을 도어락 문자에 대응
// ┌───┬───┬───┬───┐
// │ 1 │ 2 │ 3 │ A │
// │ 4 │ 5 │ 6 │ B │
// │ 7 │ 8 │ 9 │ C │
// │ * │ 0 │ # │ D │
// └───┴───┴───┴───┘
const char keyMap[16] = {
  '1','2','3','A',
  '4','5','6','B',
  '7','8','9','C',
  '*','0','#','D'
};

// --- 부저 (FQ-030) ------------------------------------------------
#define BUZZER_VCC_PIN      8    // 부저 전원 (HIGH로 켜기)
#define BUZZER_IO_PIN       4    // 부저 톤 출력 (PWM~)

// --- LED ---- 현재 미연결 ------------------------------------------
#define LED_STATUS_PIN      A5
#define LED_ACTIVE          false

// --- 릴레이 --- 현재 미연결 ----------------------------------------
#define RELAY_PIN           A1
#define RELAY_LOCKED        LOW
#define RELAY_UNLOCKED      HIGH
#define DOOR_OPEN_MS        3000
#define RELAY_ACTIVE        false

// ╔══════════════════════════════════════════════════════════╗
// ║  END OF PIN CONFIGURATION                               ║
// ╚══════════════════════════════════════════════════════════╝

// --- 음계 정의 (Hz) ------------------------------------------------
#define NOTE_C4   262
#define NOTE_E4   330
#define NOTE_F4   349
#define NOTE_G4   392
#define NOTE_A4   440
#define NOTE_C5   523
#define NOTE_E5   659
#define NOTE_G5   784

// --- 전역 변수 -----------------------------------------------------
#if NFC_ACTIVE
MFRC522 mfrc522(NFC_SS_PIN, NFC_RST_PIN);
#endif

String inputPassword = "";
const int MAX_PASSWORD_LEN = 8;
const int MIN_PASSWORD_LEN = 4;

bool doorOpen = false;
unsigned long doorOpenedAt = 0;
char lastKey = 0;               // 키 반복 방지용

// ====================================================================
//  TTP229 키패드 읽기
// ====================================================================

// TTP229 프로토콜: SCL을 16번 펄스하면서 SDO에서 비트를 읽는다.
// SDO가 LOW인 비트가 눌린 키이다 (active-LOW).
char readKeypad() {
  // SDO가 HIGH면 아무 키도 안 눌린 상태
  if (digitalRead(KP_SDO_PIN) == HIGH) {
    lastKey = 0;     // 키 해제
    return 0;
  }

  delayMicroseconds(10);   // 데이터 안정화

  char pressed = 0;
  for (int i = 0; i < 16; i++) {
    digitalWrite(KP_SCL_PIN, LOW);
    delayMicroseconds(10);

    if (digitalRead(KP_SDO_PIN) == LOW && pressed == 0) {
      pressed = keyMap[i];
    }

    digitalWrite(KP_SCL_PIN, HIGH);
    delayMicroseconds(10);
  }

  // 같은 키가 계속 눌려있으면 중복 입력 방지
  if (pressed == lastKey) return 0;
  lastKey = pressed;

  return pressed;
}

// ====================================================================
//  부저 함수 (FQ-030: VCC 핀으로 전원, IO 핀으로 톤)
// ====================================================================

void buzzerOn() {
  digitalWrite(BUZZER_VCC_PIN, HIGH);
}

void buzzerOff() {
  noTone(BUZZER_IO_PIN);
  digitalWrite(BUZZER_VCC_PIN, LOW);
}

void buzzKeypress() {
  buzzerOn();
  tone(BUZZER_IO_PIN, NOTE_C5, 30);
  delay(40);
  buzzerOff();
}

void buzzSuccess() {
  buzzerOn();
  tone(BUZZER_IO_PIN, NOTE_C5, 100);
  delay(120);
  tone(BUZZER_IO_PIN, NOTE_E5, 100);
  delay(120);
  tone(BUZZER_IO_PIN, NOTE_G5, 200);
  delay(220);
  buzzerOff();
}

void buzzFail() {
  buzzerOn();
  tone(BUZZER_IO_PIN, NOTE_A4, 250);
  delay(280);
  tone(BUZZER_IO_PIN, NOTE_F4, 400);
  delay(420);
  buzzerOff();
}

void buzzSystemReady() {
  buzzerOn();
  tone(BUZZER_IO_PIN, NOTE_E5, 80);
  delay(100);
  tone(BUZZER_IO_PIN, NOTE_G5, 80);
  delay(100);
  buzzerOff();
}

void buzzLockdown() {
  buzzerOn();
  for (int i = 0; i < 5; i++) {
    tone(BUZZER_IO_PIN, NOTE_A4, 100);
    delay(150);
    noTone(BUZZER_IO_PIN);
    delay(50);
  }
  buzzerOff();
}

// ====================================================================
//  LED 함수
// ====================================================================

void ledOn() {
  if (LED_ACTIVE) digitalWrite(LED_STATUS_PIN, HIGH);
}

void ledOff() {
  if (LED_ACTIVE) digitalWrite(LED_STATUS_PIN, LOW);
}

void ledFlash(int count, int onMs, int offMs) {
  if (!LED_ACTIVE) return;
  for (int i = 0; i < count; i++) {
    ledOn();  delay(onMs);
    ledOff(); delay(offMs);
  }
}

// ====================================================================
//  Setup
// ====================================================================

void setup() {
  Serial.begin(9600);

  #if NFC_ACTIVE
  SPI.begin();
  mfrc522.PCD_Init();
  #endif

  // TTP229 키패드 핀 초기화
  pinMode(KP_SCL_PIN, OUTPUT);
  pinMode(KP_SDO_PIN, INPUT);
  digitalWrite(KP_SCL_PIN, HIGH);  // SCL 기본 HIGH

  // 부저 핀 초기화
  pinMode(BUZZER_VCC_PIN, OUTPUT);
  pinMode(BUZZER_IO_PIN, OUTPUT);
  digitalWrite(BUZZER_VCC_PIN, LOW);

  // LED 핀 초기화
  if (LED_ACTIVE) {
    pinMode(LED_STATUS_PIN, OUTPUT);
  }

  // 릴레이 핀 초기화
  if (RELAY_ACTIVE) {
    pinMode(RELAY_PIN, OUTPUT);
    digitalWrite(RELAY_PIN, RELAY_LOCKED);
  }

  ledOn();
  buzzSystemReady();

  Serial.println("SYSTEM_READY");
}

// ====================================================================
//  Main Loop
// ====================================================================

void loop() {
  serviceDoorTimer();
  #if NFC_ACTIVE
  handleNfc();
  #endif
  handleKeypad();
  handleServerCommand();
  delay(50);    // TTP229 안정성을 위한 루프 딜레이
}

// ====================================================================
//  NFC 처리 (NFC_ACTIVE == false 이면 컴파일에서 제외)
// ====================================================================

#if NFC_ACTIVE
void handleNfc() {
  if (!mfrc522.PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial()) {
    return;
  }

  String uid = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    if (mfrc522.uid.uidByte[i] < 0x10) uid += "0";
    uid += String(mfrc522.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();

  buzzKeypress();
  Serial.print("WAKEUP:NFC:");
  Serial.println(uid);

  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1();
}
#endif

// ====================================================================
//  키패드 처리 (TTP229 터치 키패드)
// ====================================================================

void handleKeypad() {
  char key = readKeypad();
  if (!key) return;

  buzzKeypress();

  // 시리얼 모니터에도 표시 (디버깅용)
  Serial.print("[KEY] ");
  Serial.println(key);

  if (key == '*') {
    inputPassword = "";
    Serial.println("[KEY] Password cleared");
    return;
  }

  if (key == '#') {
    sendPassword();
    return;
  }

  if (inputPassword.length() < MAX_PASSWORD_LEN) {
    inputPassword += key;
    // 입력 중 피드백 (자릿수만 표시, 값은 숨김)
    Serial.print("[KEY] Input length: ");
    Serial.println(inputPassword.length());
  }
  if (inputPassword.length() >= MIN_PASSWORD_LEN) {
    sendPassword();
  }
}

void sendPassword() {
  if (inputPassword.length() == 0) return;
  Serial.print("WAKEUP:PW:");
  Serial.println(inputPassword);
  inputPassword = "";
}

// ====================================================================
//  서버 명령 수신
// ====================================================================

void handleServerCommand() {
  if (Serial.available() <= 0) return;

  String command = Serial.readStringUntil('\n');
  command.trim();

  if (command == "OPEN_DOOR" || command == "ACTION:OPEN") {
    buzzSuccess();
    ledFlash(2, 100, 80);
    ledOn();
    openDoor();
  }
  else if (command == "AUTH_FAIL") {
    buzzFail();
    ledFlash(4, 80, 80);
    ledOn();
  }
  else if (command == "LOCKDOWN") {
    buzzLockdown();
    ledFlash(10, 50, 50);
    ledOn();
  }
}

// ====================================================================
//  도어 제어
// ====================================================================

void openDoor() {
  if (RELAY_ACTIVE) {
    digitalWrite(RELAY_PIN, RELAY_UNLOCKED);
  }
  doorOpen = true;
  doorOpenedAt = millis();
  Serial.println("DOOR_OPENED");
}

void serviceDoorTimer() {
  if (doorOpen && millis() - doorOpenedAt >= DOOR_OPEN_MS) {
    if (RELAY_ACTIVE) {
      digitalWrite(RELAY_PIN, RELAY_LOCKED);
    }
    doorOpen = false;
    ledOff();
    delay(100);
    ledOn();
    Serial.println("DOOR_CLOSED");
  }
}
