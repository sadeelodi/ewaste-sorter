# ewaste-sorter

Overview

This project implements a real-time automated system for classifying and sorting e-waste using computer vision and a Raspberry Pi–based control system. The system integrates a conveyor belt, a camera, and GPIO-controlled actuators to detect, classify, and physically separate items.

System Workflow

1. The conveyor belt moves items toward a fixed scanning position.
2. A position sensor detects when an item reaches the scan point.
3. The system stops the belt and captures an image using a camera.
4. The image is processed by a trained deep learning model.
5. Based on the classification, the system activates the appropriate actuator.
6. Items are routed either directly to a bin or to a secondary sorting stage.

Classification Pipeline

The system performs sorting in two stages:

Stage 1

 -Items classified as e-waste are redirected to a secondary track.
 -Non e-waste items are advanced a fixed distance and then pushed to a separate bin.
 
 Stage 2
 E-waste items are further classified into:

  - Recyclable
  - Non-recyclable
 Each category is routed to a dedicated bin using separate actuators.

Implementation Details

Hardware Control

* GPIO pins are configured using BCM numbering.
* A relay controls the conveyor belt motor.
* Digital input is used for the position sensor.
* Output pins control four actuators (pushers).

Computer Vision

* Frames are captured using OpenCV.
* Images are resized and normalized before inference.
* The model is loaded using OpenCV’s DNN module.

Decision Logic

* The classification result determines actuator selection.
* Conveyor movement distance is approximated using time-based control:

  time = distance / speed

Key Functions

* `wait_for_item()` — monitors the sensor and stops the belt at the scan position
* `capture_frame()` — captures a frame from the camera
* `classify_item()` — processes the frame and returns a predicted label
* `advance_belt_cm()` — moves the belt a fixed distance
* `stage_one()` — performs primary sorting
* `stage_two()` — performs secondary sorting

 Requirements

* Python 3
* OpenCV
* NumPy
* RPi.GPIO

Configuration

* Update `MODEL_PATH` with the path to the trained model file.
* Adjust `belt_speed_cm_per_sec` to match the physical system.
* GPIO pin assignments should match the hardware wiring.

Notes

* Model training is handled separately and is not included in this repository.
* System timing may require calibration depending on load and hardware conditions.
* The system is designed for continuous operation and includes safe shutdown handling.

