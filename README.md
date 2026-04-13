# ewaste-sorter

## Overview

This project implements a real-time automated system for classifying and sorting e-waste using computer vision and a Raspberry Pi-based control system. It combines a conveyor belt, a camera, a position sensor, and GPIO-controlled actuators to detect, classify, and physically separate items.

## How It Works

1. The conveyor belt moves an item to a fixed scanning position.
2. A position sensor detects when the item reaches the scan point.
3. The belt stops and the camera captures an image.
4. The image is passed to a trained deep learning model.
5. The predicted class determines which actuator should fire.
6. The item is routed either directly to a bin or to a second sorting stage.

## Classification Pipeline

The sorter works in two stages.

### Stage 1: E-waste vs non-e-waste

- Items classified as e-waste are redirected to the secondary track.
- Non-e-waste items are moved forward a fixed distance and then pushed into a separate bin.

### Stage 2: E-waste subtype

- E-waste items are classified as either `recyclable_ewaste` or `non_recyclable_ewaste`.
- Each category is routed to its own bin using a dedicated actuator.

## Requirements

### Runtime

- Python 3
- OpenCV
- NumPy
- RPi.GPIO

Install runtime dependencies with:

```bash
pip install -r requirements.txt
```

## Runtime Configuration

Before running the sorter:

- Update `MODEL_PATH` with the path to the trained model file.
- Adjust `belt_speed_cm_per_sec` to match the physical conveyor speed.
- Make sure the GPIO pin assignments match the actual hardware wiring.

## Implementation Details

### Hardware Control

- GPIO pins use BCM numbering.
- A relay controls the conveyor belt motor.
- A digital input pin reads the position sensor.
- Four output pins control the pushers.

### Computer Vision

- Frames are captured using OpenCV.
- Images are resized to `224 x 224` before inference.
- The model is loaded with OpenCV's DNN module.

### Decision Logic

- The predicted class determines actuator selection.
- Belt movement distance is approximated using time-based control:

```text
time = distance / speed
```

## Key Functions

- `wait_for_item()` monitors the sensor and stops the belt at the scan position.
- `capture_frame()` captures a frame from the camera.
- `classify_item()` processes the frame and returns a predicted label.
- `advance_belt_cm()` moves the belt a fixed distance.
- `stage_one()` performs primary sorting.
- `stage_two()` performs secondary sorting.

## Notes

- The training and inference steps are kept separate on purpose.
- System timing may require calibration depending on load and hardware behavior.
- The system is designed for continuous operation and includes safe shutdown handling.
