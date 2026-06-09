# RKCamRecord3 — PC端 Web 控制面板
# 在电脑上运行： python pc_server.py

import os
import json
import time
import uuid
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import requests
from flask import Flask, render_template, Response, request, jsonify, send_file

# ── 配置 ──────────────────────────────────────────────
BOARD_IP = "192.168.55.32"
BOARD_PORT = 5000
STREAM_URL = f"http://{BOARD_IP}:{BOARD_PORT}/stream"
PC_PORT = 5001

BASE_DIR = Path(__file__).parent
RECORDINGS_DIR = BASE_DIR / "recordings"
RECORDINGS_DIR.mkdir(exist_ok=True)

app = Flask(__name__)

# ── 录制状态 ──────────────────────────────────────────
recording = {
    "active": False,
    "paused": False,
    "frames": [],           # 缓存帧 (BGR)
    "start_time": None,
    "fps": 20,
    "filename": None,
}

# ── 读取 MJPEG 流 ────────────────────────────────────

def gen_frames():
    """从板子获取 MJPEG 流（带自动重连）"""
    retries = 0
    while True:
        try:
            stream = requests.get(STREAM_URL, stream=True, timeout=(3, 10))
            bytes_buffer = b""
            retries = 0  # 连接成功，重置重试计数
            for chunk in stream.iter_content(chunk_size=4096):
                if chunk:
                    bytes_buffer += chunk
                    a = bytes_buffer.find(b"\xff\xd8")
                    b = bytes_buffer.find(b"\xff\xd9")
                    if a != -1 and b != -1 and b > a:
                        jpg = bytes_buffer[a : b + 2]
                        bytes_buffer = bytes_buffer[b + 2 :]

                        # 如果是录制状态，缓存帧
                        if recording["active"] and not recording["paused"]:
                            frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                            if frame is not None:
                                recording["frames"].append(frame)

                        yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + jpg + b"\r\n")
        except Exception as e:
            retries += 1
            print(f"[Stream] disconnect (retry {retries}): {e}")

        # 发送占位图
        placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
        if retries > 3:
            msg = "Board offline - waiting..."
        else:
            msg = f"Reconnecting... ({retries})"
        cv2.putText(placeholder, msg, (120, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        _, jpg = cv2.imencode(".jpg", placeholder)
        yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + jpg.tobytes() + b"\r\n")
        time.sleep(2)


# ── 路由 ─────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html", board_ip=BOARD_IP)


@app.route("/stream")
def video_stream():
    return Response(gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/status")
def stream_status():
    """检查板子流是否在线"""
    try:
        r = requests.get(f"http://{BOARD_IP}:{BOARD_PORT}/status", timeout=3)
        return jsonify({"online": True, "board": r.json()})
    except Exception:
        return jsonify({"online": False})


@app.route("/record/start", methods=["POST"])
def start_recording():
    """开始录制"""
    if recording["active"]:
        return jsonify({"error": "已经在录制中"}), 400

    data = request.get_json(silent=True) or {}
    filename = data.get("filename", "").strip()
    if not filename:
        filename = f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    recording["active"] = True
    recording["paused"] = False
    recording["frames"] = []
    recording["start_time"] = time.time()
    recording["filename"] = filename

    return jsonify({"status": "started", "filename": filename})


@app.route("/record/pause", methods=["POST"])
def pause_recording():
    """暂停 / 恢复录制"""
    if not recording["active"]:
        return jsonify({"error": "未在录制"}), 400

    recording["paused"] = not recording["paused"]
    return jsonify({"paused": recording["paused"]})


@app.route("/record/stop", methods=["POST"])
def stop_recording():
    """停止录制并保存视频"""
    if not recording["active"]:
        return jsonify({"error": "未在录制"}), 400

    recording["active"] = False
    recording["paused"] = False

    frames = recording["frames"][:]
    recording["frames"] = []
    duration = time.time() - recording["start_time"]
    filename = recording["filename"]
    recording["filename"] = None
    recording["start_time"] = None

    if not frames:
        return jsonify({"error": "没有录到帧", "frames": 0}), 400

    # 写入 MP4
    h, w = frames[0].shape[:2]
    out_path = RECORDINGS_DIR / f"{filename}.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    fps = min(recording["fps"], max(1, int(len(frames) / duration))) if duration > 0 else recording["fps"]
    writer = cv2.VideoWriter(str(out_path), fourcc, fps, (w, h))

    for f in frames:
        writer.write(f)
    writer.release()

    # 生成元数据
    meta = {
        "filename": f"{filename}.mp4",
        "frames": len(frames),
        "duration": round(duration, 1),
        "fps": fps,
        "resolution": f"{w}x{h}",
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    meta_path = RECORDINGS_DIR / f"{filename}.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    return jsonify({"status": "saved", "file": f"{filename}.mp4", **meta})


@app.route("/recordings")
def list_recordings():
    """列出所有录制文件"""
    files = []
    for f in sorted(RECORDINGS_DIR.glob("*.mp4"), key=os.path.getmtime, reverse=True):
        meta_path = RECORDINGS_DIR / f"{f.stem}.json"
        meta = {}
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as mf:
                meta = json.load(mf)
        files.append({
            "name": f.name,
            "stem": f.stem,
            "size": round(f.stat().st_size / (1024 * 1024), 2),
            "size_unit": "MB",
            "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            "duration": meta.get("duration", "?"),
            "fps": meta.get("fps", "?"),
            "resolution": meta.get("resolution", "?"),
            "frames": meta.get("frames", "?"),
        })
    return jsonify(files)


@app.route("/recordings/download/<name>")
def download_recording(name):
    """下载录制文件"""
    safe_path = RECORDINGS_DIR / name
    if not safe_path.exists() or safe_path.suffix != ".mp4":
        return jsonify({"error": "文件不存在"}), 404
    return send_file(str(safe_path), as_attachment=True, download_name=name)


@app.route("/recordings/rename", methods=["POST"])
def rename_recording():
    """重命名录制文件"""
    data = request.get_json(silent=True) or {}
    old_name = data.get("old_name", "")
    new_name = data.get("new_name", "")

    if not old_name or not new_name:
        return jsonify({"error": "参数缺失"}), 400

    old_path = RECORDINGS_DIR / old_name
    if not old_path.exists():
        return jsonify({"error": "原文件不存在"}), 404

    # 确保扩展名
    if not new_name.lower().endswith(".mp4"):
        new_name += ".mp4"
    new_path = RECORDINGS_DIR / new_name

    if new_path.exists():
        return jsonify({"error": "文件名已存在"}), 409

    old_path.rename(new_path)

    # 重命名关联的元数据
    old_meta = RECORDINGS_DIR / f"{old_path.stem}.json"
    if old_meta.exists():
        old_meta.rename(RECORDINGS_DIR / f"{new_path.stem}.json")
        with open(RECORDINGS_DIR / f"{new_path.stem}.json", "r+", encoding="utf-8") as f:
            meta = json.load(f)
            meta["filename"] = new_path.name
            f.seek(0)
            json.dump(meta, f, ensure_ascii=False, indent=2)
            f.truncate()

    return jsonify({"status": "renamed", "file": new_path.name})


@app.route("/recordings/delete", methods=["POST"])
def delete_recording():
    """删除录制文件"""
    data = request.get_json(silent=True) or {}
    name = data.get("name", "")
    path = RECORDINGS_DIR / name
    if path.exists():
        path.unlink()
        # 删除元数据
        meta_path = RECORDINGS_DIR / f"{path.stem}.json"
        if meta_path.exists():
            meta_path.unlink()
        return jsonify({"status": "deleted"})
    return jsonify({"error": "文件不存在"}), 404


# ── 启动 ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("  🎥 RKCamRecord3 — PC 端控制面板")
    print(f"  板子: {BOARD_IP}:{BOARD_PORT}")
    print(f"  本地: http://localhost:{PC_PORT}")
    print(f"  录制保存: {RECORDINGS_DIR}")
    print("=" * 55)
    app.run(host="0.0.0.0", port=PC_PORT, debug=False, threaded=True)
