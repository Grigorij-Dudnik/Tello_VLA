import pickle
import socket
import time

import cv2
from djitellopy import Tello


SERVER = "greg-pc"
PORT = 5005
FPS = 30
SPEED = 25


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

try:
    tello.takeoff()
    while True:
        loop_start = time.perf_counter()
        rgb = cv2.resize(frames.frame, (640, 480))
        encode_start = time.perf_counter()
        _, jpg = cv2.imencode(".jpg", rgb, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
        encode_time = time.perf_counter() - encode_start

        # cv2.imshow("server jpg", cv2.imdecode(jpg, cv2.IMREAD_COLOR))
        # cv2.waitKey(1)

        send_start = time.perf_counter()
        send_msg(s, {"jpg": jpg.tobytes(), "height": tello.get_height()})
        send_time = time.perf_counter() - send_start
        wait_start = time.perf_counter()
        forward, right, up, yaw = recv_msg(s)
        wait_time = time.perf_counter() - wait_start
        tello.send_command_without_return(f"rc {int(SPEED * right)} {int(SPEED * forward)} {int(SPEED * up)} {int(SPEED * yaw)}")
        loop_time = time.perf_counter() - loop_start
        print(f"encode {encode_time:.3f}s send {send_time:.3f}s wait {wait_time:.3f}s loop {loop_time:.3f}s payload {len(jpg)} fps {1 / loop_time:.1f}")
        time.sleep(max(0, 1 / FPS - loop_time))
except KeyboardInterrupt:
    tello.land()
    s.close()
    tello.end()
