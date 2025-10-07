# Digital Abacus: AQA Engineering NEA 2026
Software for AQA8852 Engineering NEA - 2026

The ESP32-2432S028R runs on Micropython + LVGL + ESPNOW firmware.
The ESP32-S3 runs on Micropython + ESPNOW firmware.

The ESP32-S3 (sometimes reffered to in the code as "main") is used to control the motor using the L298N DC Motor driver, as the CYD lacks peripherals and pins to have the capability.


Both software must be started up on the same time in order to be synced.
