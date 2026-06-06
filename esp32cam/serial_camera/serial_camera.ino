// ESP32-CAM USB-Serial JPEG bridge for the 2FA doorlock project.
//
// Flash this to the ESP32-CAM + CH340/USB-C board. The Python server sends
// "CAPTURE\n" and receives "JPEG:<length>\n<jpeg bytes>\nEND\n".

#include "esp_camera.h"
#include <string.h>

#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27

#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

static bool cameraReady = false;
static const unsigned long SERIAL_BAUD = 921600;

static void sendError(const char *message) {
  Serial.print("ERR:");
  Serial.println(message);
}

static bool initCamera() {
  camera_config_t config = {};
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_CIF;   // 400x296 (중간 해상도, VGA보다 데이터량 크게 감소)
  config.grab_mode = psramFound() ? CAMERA_GRAB_LATEST : CAMERA_GRAB_WHEN_EMPTY;
  config.fb_location = psramFound() ? CAMERA_FB_IN_PSRAM : CAMERA_FB_IN_DRAM;
  config.jpeg_quality = 10;
  config.fb_count = psramFound() ? 2 : 1;
  config.sccb_i2c_port = 0;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("ERR:init_failed:0x%x\n", err);
    return false;
  }

  sensor_t *sensor = esp_camera_sensor_get();
  if (sensor) {
    sensor->set_framesize(sensor, psramFound() ? FRAMESIZE_VGA : FRAMESIZE_QVGA);
    sensor->set_quality(sensor, 10);
    sensor->set_vflip(sensor, 1);
    sensor->set_hmirror(sensor, 1);
  }

  return true;
}

static void warmupCamera() {
  for (int i = 0; i < 2; i++) {
    camera_fb_t *fb = esp_camera_fb_get();
    if (fb) {
      esp_camera_fb_return(fb);
    }
    delay(40);
  }
}

static void captureAndSend() {
  if (!cameraReady) {
    sendError("camera_not_ready");
    return;
  }

  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    sendError("capture_failed");
    return;
  }

  Serial.print("JPEG:");
  Serial.println(fb->len);
  Serial.write(fb->buf, fb->len);
  Serial.print("\nEND\n");
  Serial.flush();
  esp_camera_fb_return(fb);
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  Serial.setDebugOutput(false);
  delay(1200);
  cameraReady = initCamera();
  if (cameraReady) {
    warmupCamera();
    Serial.println("ESP32CAM_READY");
  } else {
    Serial.println("ERR:init_failed");
  }
}

void loop() {
  if (!Serial.available()) {
    delay(5);
    return;
  }

  char command[16] = {0};
  size_t length = Serial.readBytesUntil('\n', command, sizeof(command) - 1);
  while (length > 0 && (command[length - 1] == '\r' || command[length - 1] == '\n' || command[length - 1] == ' ')) {
    command[--length] = '\0';
  }
  for (size_t i = 0; i < length; i++) {
    if (command[i] >= 'a' && command[i] <= 'z') {
      command[i] = command[i] - 'a' + 'A';
    }
  }

  if (strcmp(command, "CAPTURE") == 0) {
    captureAndSend();
  } else if (strcmp(command, "PING") == 0) {
    Serial.println(cameraReady ? "PONG:READY" : "PONG:NOT_READY");
  } else if (length > 0) {
    sendError("unknown_command");
  }
}
