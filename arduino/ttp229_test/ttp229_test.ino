/*
 * TTP229 키패드 진단 v3
 * SDO 상태 무관하게 계속 클럭을 보내면서 읽는다.
 * 0이 나오는 비트가 눌린 키.
 */

#define KP_SDO_PIN  2
#define KP_SCL_PIN  3

void setup() {
  Serial.begin(9600);
  pinMode(KP_SCL_PIN, OUTPUT);
  pinMode(KP_SDO_PIN, INPUT_PULLUP);
  digitalWrite(KP_SCL_PIN, HIGH);
  delay(500);
  Serial.println("=== TTP229 DIAGNOSTIC v3 ===");
  Serial.println("Actively polling every 200ms...");
}

void loop() {
  // 16비트 읽기: 계속 클럭을 보낸다
  uint16_t data = 0;

  for (int i = 0; i < 16; i++) {
    digitalWrite(KP_SCL_PIN, LOW);
    delayMicroseconds(2);
    int bit = digitalRead(KP_SDO_PIN);
    if (bit == LOW) {
      data |= (1 << i);
    }
    digitalWrite(KP_SCL_PIN, HIGH);
    delayMicroseconds(2);
  }

  if (data != 0) {
    Serial.print("PRESSED: 0b");
    for (int i = 15; i >= 0; i--) {
      Serial.print((data >> i) & 1);
    }
    Serial.print(" -> key ");
    for (int i = 0; i < 16; i++) {
      if (data & (1 << i)) {
        Serial.print(i + 1);
        Serial.print(" ");
      }
    }
    Serial.println();
  }

  delay(200);
}
