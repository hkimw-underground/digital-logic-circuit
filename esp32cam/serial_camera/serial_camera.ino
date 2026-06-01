// ESP32-CAM USB-Serial JPEG bridge for the 2FA doorlock project.
//
// Flash this to the ESP32-CAM + CH340/USB-C board. The Python server sends
// "CAPTURE\n" and receives "JPEG:<length>\n<jpeg bytes>\nEND\n".

#include "esp_camera.h"

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

static void sendError(const char *message) {
  Serial.print("ERR:");
  Serial.println(message);
}

static bool initCamera() {
  camera_config_t config;
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
  config.grab_mode = CAMERA_GRAB_LATEST;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.jpeg_quality = 12;
  config.fb_count = 2;

  if (psramFound()) {
    config.frame_size = FRAMESIZE_VGA;
  } else {
    config.frame_size = FRAMESIZE_QVGA;
    config.fb_count = 1;
    config.fb_location = CAMERA_FB_IN_DRAM;
  }

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    return false;
  }

  sensor_t *sensor = esp_camera_sensor_get();
  if (sensor) {
    sensor->set_framesize(sensor, psramFound() ? FRAMESIZE_VGA : FRAMESIZE_QVGA);
    sensor->set_quality(sensor, 12);
  }

  return true;
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
  Serial.begin(921600);
  delay(1200);
  cameraReady = initCamera();
  if (cameraReady) {
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

  String command = Serial.readStringUntil('\n');
  command.trim();
  command.toUpperCase();

  if (command == "CAPTURE") {
    captureAndSend();
  } else if (command == "PING") {
    Serial.println(cameraReady ? "PONG:READY" : "PONG:NOT_READY");
  } else if (command.length() > 0) {
    sendError("unknown_command");
  }
}
