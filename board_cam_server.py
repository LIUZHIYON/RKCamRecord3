# RKCamRecord3 — RK3576 Camera Server v4 (稳定版)
# 专用读帧线程 + threaded Flask
import os, sys, time, signal
from threading import Thread, Lock
import cv2, numpy as np
from flask import Flask, Response, jsonify

CAMERA_INDEX = 11
FRAME_W = 1280
FRAME_H = 720
FPS_LIMIT = 15
JPEG_Q = 60
PORT = 5000

app = Flask(__name__)

# 全局帧缓存
frame_lock = Lock()
current_frame = None
running = True
camera = None
cam_online = False

def camera_worker():
    """后台线程 — 持续读帧"""
    global current_frame, camera, cam_online, running
    while running:
        try:
            if camera is None or not camera.isOpened():
                with frame_lock:
                    if camera:
                        camera.release()
                cap = cv2.VideoCapture(CAMERA_INDEX)
                if cap.isOpened():
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_W)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_H)
                    cap.set(cv2.CAP_PROP_FPS, FPS_LIMIT)
                    with frame_lock:
                        camera = cap
                    print(f"[Camera] opened /dev/video{CAMERA_INDEX}")
                else:
                    time.sleep(1)
                    continue

            with frame_lock:
                if camera is None:
                    continue
                ret, frame = camera.read()
                if ret:
                    current_frame = frame
                    cam_online = True
                else:
                    # 读帧失败，尝试重开
                    print("[Camera] read failed, reopening...")
                    camera.release()
                    camera = None
                    cam_online = False
                    time.sleep(1)
        except Exception as e:
            print(f"[Camera] error: {e}")
            time.sleep(1)

    # 清理
    with frame_lock:
        if camera:
            camera.release()


@app.route("/")
def index():
    return jsonify({"service": "RKCamRecord3 v4", "online": cam_online})


@app.route("/status")
def status():
    w, h = 0, 0
    with frame_lock:
        online = cam_online and camera is not None
        if online:
            try:
                w = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            except:
                pass
    return jsonify({
        "camera_online": online,
        "device": f"video{CAMERA_INDEX}",
        "resolution": f"{w}x{h}",
    })


@app.route("/stream")
def stream():
    def gen():
        global current_frame
        while True:
            try:
                with frame_lock:
                    f = current_frame
                if f is None:
                    blank = np.zeros((FRAME_H, FRAME_W, 3), dtype=np.uint8)
                    cv2.putText(blank, "No Signal", (FRAME_W//2-120, FRAME_H//2),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255,255,255), 2)
                    _, jpg = cv2.imencode(".jpg", blank, [cv2.IMWRITE_JPEG_QUALITY, JPEG_Q])
                    yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpg.tobytes() + b"\r\n"
                    time.sleep(0.5)
                    continue

                _, jpg = cv2.imencode(".jpg", f, [cv2.IMWRITE_JPEG_QUALITY, JPEG_Q])
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpg.tobytes() + b"\r\n"
                time.sleep(1 / FPS_LIMIT)
            except GeneratorExit:
                break
            except Exception as e:
                print(f"[Stream] {e}")
                time.sleep(0.5)

    return Response(gen(),
                    mimetype="multipart/x-mixed-replace; boundary=frame",
                    headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.route("/restart", methods=["POST"])
def restart_cam():
    global camera
    with frame_lock:
        if camera:
            camera.release()
        camera = None
    return jsonify({"ok": True})


if __name__ == "__main__":
    print("=" * 50)
    print("  RKCamRecord3 v4 -- Camera Server")
    print("=" * 50)

    t = Thread(target=camera_worker, daemon=True)
    t.start()
    time.sleep(2)

    print(f"  Camera: /dev/video{CAMERA_INDEX}")
    print(f"  Stream: http://0.0.0.0:{PORT}/stream")
    print(f"  Status: http://0.0.0.0:{PORT}/status")
    print()

    app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True)
