import shutil
import time
from ctypes import windll

import cv2
import numpy as np
from djitellopy import Tello
from lerobot.datasets.lerobot_dataset import LeRobotDataset


DATASET_REPO = "Grigorij/Tello_red_apple"
ROOT = "dataset/Tello_red_apple"
TASK = "Fly to the red apple"
FPS = 30
SPEED = 35

features = {
    "observation.images.camera_front": {"dtype": "video", "shape": (480, 640, 3), "names": ["height", "width", "channels"]},
    "observation.state": {"dtype": "float32", "shape": (1,), "names": ["height"]},
    "action": {"dtype": "float32", "shape": (4,), "names": ["forward", "right", "up", "yaw"]},
}
pressed = lambda c: int(bool(windll.user32.GetAsyncKeyState(ord(c)) & 0x8000))

shutil.rmtree(ROOT, ignore_errors=True)
dataset = LeRobotDataset.create(DATASET_REPO, fps=FPS, features=features, root=ROOT)
tello = Tello()
tello.connect()
print("battery", tello.get_battery())
tello.streamon()
frames = tello.get_frame_read()
time.sleep(1)
tello.takeoff()
recording = False
episode_frames = 0

while True:
    rgb = cv2.resize(frames.frame, (640, 480))
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    cv2.imshow("tello keyboard recorder", bgr)
    cv2.waitKey(1)

    if pressed("B"):
        recording = False
        print(f"Battery: {tello.get_battery()}%")
        print("Finishing episode, reset")
    if pressed("N") and not recording:
        if episode_frames:
            dataset.save_episode()
            episode_frames = 0
        print("Starting new episode")
        recording = True
    if pressed("X"):
        break

    forward = pressed("W") - pressed("S")
    right = pressed("D") - pressed("A")
    up = pressed("R") - pressed("F")
    yaw = pressed("E") - pressed("Q")
    tello.send_command_without_return(f"rc {SPEED * right} {SPEED * forward} {SPEED * up} {SPEED * yaw}")
    if recording:
        dataset.add_frame({
            "observation.images.camera_front": rgb,
            "observation.state": np.array([tello.get_height()], dtype=np.float32),
            "action": np.array([forward, right, up, yaw], dtype=np.float32),
            "task": TASK,
        })
        episode_frames += 1
    time.sleep(1 / FPS)

tello.land()
if episode_frames:
    dataset.save_episode()
dataset.finalize()
tello.end()
cv2.destroyAllWindows()
