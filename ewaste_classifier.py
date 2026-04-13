# OpenCV - for camera recognition 
import cv2
# numpy -  math on arrays (to find which label scored highest)
import numpy as np
# RPi.GPIO - to let python talk to the physical pins on the raspberry pi
import RPi.GPIO as GPIO
# time -to pause the programme (when moving the belt)
import time


# Pin Numbers
# I'm using BCM - the chip's numbering system not the borad's

BELT_PIN = 17           # pin connected to the belt motor relay
POSITION_SENSOR = 27    # pin connected to sensor that detects when item is at scan spot
PUSHER_1_PIN = 22       # stage 1: pushes ewaste off to the stage 2 track
PUSHER_2_PIN = 23       # stage 1: pushes non-ewaste to bin (after 20cm forward)
PUSHER_3_PIN = 24       # stage 2: pushes recyclable ewaste to its bin
PUSHER_4_PIN = 25       # stage 2: pushes non-recyclable ewaste to its bin

# confirm using BCM pin numbering
GPIO.setmode(GPIO.BCM)
# turn off warning messages when we re-run the script
GPIO.setwarnings(False)

# OUT = we are SeENDING a signal TO this pin (we control it)
GPIO.setup(BELT_PIN, GPIO.OUT)
# IN = we are READING FROM this pin (it sends us info)
GPIO.setup(POSITION_SENSOR, GPIO.IN)
# all pushers are outputs because we send signal to them
GPIO.setup(PUSHER_1_PIN, GPIO.OUT)
GPIO.setup(PUSHER_2_PIN, GPIO.OUT)
GPIO.setup(PUSHER_3_PIN, GPIO.OUT)
GPIO.setup(PUSHER_4_PIN, GPIO.OUT)


# Camera Setup

# 0 = use the first camera connected to the pi
camera = cv2.VideoCapture(0)
# set frame width to 640 pixels
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
# set frame height to 480 pixels
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
# After testing we concluded that 640*480 gives us a goodframe with reliable accurancy


# Model Setup

# NOTE: model training was handled separately - this script just loads and uses it
# the model keeps improving so make sure this always points to the latest version
# MODEL LINK SHOULD GO HERE:
MODEL_PATH = "PUT_MODEL_PATH_HERE"

# the 3 categories the model can classify - order matches how model was trained
CLASS_LABELS = ["non_ewaste", "recyclable_ewaste", "non_recyclable_ewaste"]

# load the model from the path above into memory so we can use it
net = cv2.dnn.readNet(MODEL_PATH)


# Belt Controls

def start_belt():
    # HIGH = send power to the pin -> turn motor on
    GPIO.output(BELT_PIN, GPIO.HIGH)
    print("[belt] started")  # debug

def stop_belt():
    # LOW = cut power to the pin -> turn motor off
    GPIO.output(BELT_PIN, GPIO.LOW)
    print("[belt] stopped")  # debug


# Pusher

def activate_pusher(pin, duration=0.5):
    # duration = how many seconds the pusher stays extended before pulling back
    print(f"[pusher] activating pin {pin}")  # debug - tells me which pusher fired

    # send power to extend the pusher
    GPIO.output(pin, GPIO.HIGH)
    # wait for pusher to push item fully off the belt
    time.sleep(duration)
    # cut power to take pusher back
    GPIO.output(pin, GPIO.LOW)
    # short pause so item fully clears before belt starts again
    time.sleep(0.3)


# Wait for the Item to reach sacn position

def wait_for_item():
    print("[sensor] waiting for item...")
    # turn belt on so item starts moving toward the scan position
    start_belt()

    # keep checking sensor every 0.05 seconds
    # GPIO.LOW means nothing detected yet
    # when item arrives sensor switches to HIGH and we exit the loop
    while GPIO.input(POSITION_SENSOR) == GPIO.LOW:
        time.sleep(0.05)  # small sleep so we don't check a million times per second

    # item arrived - stop belt so item stays still for the photo
    stop_belt()
    print("[sensor] item detected!")  # this part works confirmed


# Capture photo

def capture_frame():
    # camera.read() grabs one frame from the camera
    # ret = True if successful, else False
    # frame = the actual image as a big grid of pixel values
    ret, frame = camera.read()

    if not ret:
        # if this prints, something is wrong with the camera connection
        print("[camera] ERROR - could not read frame")
        raise RuntimeError("camera read failed")

    print("[camera] frame captured")  # debug
    return frame


# Classify the Item

def classify_item(frame):
    # the model can't take a raw image - we convert it to a "blob" first
    # blob - the image reformatted and normalized so the model understands it
    blob = cv2.dnn.blobFromImage(
        frame,
        scalefactor=1.0 / 255.0,  # shrink pixel values from 0-255 range down to 0-1 range
        size=(224, 224),           # resize image to 224x224 because that's what the model expects
        mean=(0, 0, 0),            # no mean subtraction needed for this model
        swapRB=True,               # opencv uses BGR color order, model expects RGB so we swap
        crop=False                 # don't crop, just resize
    )

    # give the blob to the model as input
    net.setInput(blob)
    # run the model - outputs is a list of confidence scores, one per class
    outputs = net.forward()

    # argmax finds the index of the highest score = the most likely class
    predicted_index = int(np.argmax(outputs[0]))
    # get how confident the model is (0 to 1, higher = more sure)
    confidence = float(outputs[0][predicted_index])
    # use the index to get the actual label name from our list
    label = CLASS_LABELS[predicted_index]

    # print to terminal so i can see what got classified and how confident in real time
    print(f"[model] classified as: {label} | confidence: {confidence:.2f}")

    # TODO: maybe add a confidence threshold later
    # idea: if confidence < 0.7 skip sorting and send to manual check bin

    return label


# Advance Belt A SPECIFIC Distance

def advance_belt_cm(cm, belt_speed_cm_per_sec=5.0):
    # we can't measure distance directly so we calculate how long to run the belt
    # formula: time = distance / speed
    # belt_speed_cm_per_sec may need tuning depending on how heavy items are
    duration = cm / belt_speed_cm_per_sec
    print(f"[belt] advancing {cm}cm (running for {duration:.2f}s)")  # debug

    start_belt()
    # run belt for exactly that many seconds to move the item the right distance
    time.sleep(duration)
    stop_belt()


# Stage 1 : e-waste or not?

def stage_one(label):
    if label in ("recyclable_ewaste", "non_recyclable_ewaste"):
        # it's ewaste - push it sideways to the stage 2 track
        print("[stage1] ewaste -> pusher 1")
        activate_pusher(PUSHER_1_PIN)
        return True  # tell main() we need stage 2

    else:
        # not ewaste - move it 20cm further down then push to non-ewaste bin
        print("[stage1] not ewaste -> advancing 20cm then pusher 2")
        advance_belt_cm(20)
        activate_pusher(PUSHER_2_PIN)
        return False  # tell main() we're done, no stage 2 needed


# Stage 2:recyclable or not-recyclable e-waste?

def stage_two(label):
    # only e-waste items reach this function
    if label == "recyclable_ewaste":
        print("[stage2] recyclable -> pusher 3")
        activate_pusher(PUSHER_3_PIN)
    else:
        print("[stage2] non recyclable -> pusher 4")
        activate_pusher(PUSHER_4_PIN)


# Mail Loop

def main():
    print("ewaste sorter starting ")
    try:
        while True:
            # step 1 - run belt until item reaches scan position
            wait_for_item()

            # small pause so item is fully still before we take the photo
            time.sleep(0.2)

            # step 2 - take photo
            frame = capture_frame()

            # step 3 - run photo through model to get classification
            label = classify_item(frame)

            # step 4 - stage 1: separate ewaste from non-ewaste
            is_ewaste = stage_one(label)

            # step 5 - stage 2: only runs if item was ewaste
            if is_ewaste:
                # wait a moment for item to reach the stage 2 sensor position
                time.sleep(0.5)
                stage_two(label)

            # pause before we start looking for the next item
            # might need to adjust depending on how fast items come in
            time.sleep(1.0)

    except KeyboardInterrupt:
        # ctrl+c was pressed - shut everything down cleanly
        print("\n[main] shutting down - keyboard interrupt")
    finally:
        # always release camera and clean up gpio pins when done
        # this prevents errors if we run the script again
        camera.release()
        GPIO.cleanup()
        print("[main] cleanup done")


if __name__ == "__main__":
    main()
