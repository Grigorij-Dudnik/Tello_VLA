import pickle
import socket
import time

import cv2
from djitellopy import Tello


SERVER = "greg-pc"
PORT = 5005
FPS = 30
SPEED = 35
JPEG_QUALITY = 60


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
s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
s.connect((SERVER, PORT))
print(recv_msg(s))

tello = Tello()
tello.connect()
print("battery", tello.get_battery())
tello.streamon()
frames = tello.get_frame_read()
time.sleep(1)
tello.takeoff()
t = time.perf_counter()

while True:
    loop_start = time.perf_counter()
    rgb = cv2.resize(frames.frame, (640, 480))
    # cv2.imshow("tello", cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
    # cv2.waitKey(1)
    encode_start = time.perf_counter()
    _, jpg = cv2.imencode(".jpg", rgb, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])
    encode_time = time.perf_counter() - encode_start
    send_start = time.perf_counter()
    send_msg(s, {"jpg": jpg.tobytes(), "height": tello.get_height()})
    send_time = time.perf_counter() - send_start
    wait_start = time.perf_counter()
    forward, right, up, yaw = recv_msg(s)
    wait_time = time.perf_counter() - wait_start
    tello.send_command_without_return(f"rc {int(SPEED * right)} {int(SPEED * forward)} {int(SPEED * up)} {int(SPEED * yaw)}")
    loop_time = time.perf_counter() - loop_start
    print(f"encode {encode_time:.3f}s send {send_time:.3f}s wait {wait_time:.3f}s loop {loop_time:.3f}s payload {len(jpg)}")
    print(1 / (time.perf_counter() - t))
    t = time.perf_counter()
    time.sleep(max(0, 1 / FPS - loop_time))
