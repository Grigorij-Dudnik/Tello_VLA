import pickle
import socket
import time

import cv2
from djitellopy import Tello


SERVER = "greg-pc"
PORT = 5005
FPS = 30
SPEED = 35


def recv_msg(conn):
    hdr = b""
    while len(hdr) < 4:
        hdr += conn.recv(4 - len(hdr))
    data = b""
    size = int.from_bytes(hdr, "big")
    while len(data) < size:
        data += conn.recv(size - len(data))
    return pickle.loads(data)


def send_msg(conn, msg):
    data = pickle.dumps(msg)
    conn.sendall(len(data).to_bytes(4, "big") + data)


s = socket.socket()
s.connect((SERVER, PORT))
print(recv_msg(s))

tello = Tello()
tello.connect()
print("battery", tello.get_battery())
tello.streamon()
frames = tello.get_frame_read()
time.sleep(1)
tello.takeoff()

while True:
    rgb = frames.frame
    cv2.imshow("tello", cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
    cv2.waitKey(1)
    send_msg(s, {"rgb": rgb, "height": tello.get_height()})
    forward, right, up, yaw = recv_msg(s)
    tello.send_command_without_return(f"rc {int(SPEED * right)} {int(SPEED * forward)} {int(SPEED * up)} {int(SPEED * yaw)}")
    time.sleep(1 / FPS)
