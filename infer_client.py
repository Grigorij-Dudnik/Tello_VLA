import pickle
import socket
import time

from djitellopy import Tello


SERVER = "greg-pc"
PORT = 5005
FPS = 30
SPEED = 35

s = socket.socket()
s.connect((SERVER, PORT))
f = s.makefile("rwb")

tello = Tello()
tello.connect()
print("battery", tello.get_battery())
tello.streamon()
frames = tello.get_frame_read()
time.sleep(1)
tello.takeoff()

while True:
    pickle.dump({"rgb": frames.frame, "height": tello.get_height()}, f)
    f.flush()
    forward, right, up, yaw = pickle.load(f)
    tello.send_command_without_return(f"rc {int(SPEED * right)} {int(SPEED * forward)} {int(SPEED * up)} {int(SPEED * yaw)}")
    time.sleep(1 / FPS)
