#!/usr/bin/env python3
"""RKCamRecord3 v8 — 稳定录像 + 实时推流 + 文件下载"""
import cv2, os, sys, time, threading
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GLib', '2.0')
from gi.repository import Gst, GLib
from flask import Flask, Response, jsonify, send_file, abort

CAMERA = 11; W, H = 1920, 1080; FPS = 24; JPEG_Q = 75; PORT = 5000
REC_DIR = "/home/cat/recordings"
os.makedirs(REC_DIR, exist_ok=True)
Gst.init(None)

frame_lock = threading.Lock()
current_frame = None; cam_online = False; recording = False; recorder = None

class CameraWorker:
    def __init__(self):
        self.cap = None; self.running = True; self.thread = None
    def start(self):
        self.thread = threading.Thread(target=self._run, daemon=True); self.thread.start()
    def _run(self):
        global current_frame, cam_online
        while self.running:
            try:
                if self.cap is None or not self.cap.isOpened():
                    cap = cv2.VideoCapture(CAMERA)
                    if cap.isOpened():
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, W)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, H)
                        cap.set(cv2.CAP_PROP_FPS, FPS)
                        self.cap = cap
                        print(f"[Camera] /dev/video{CAMERA} — {W}x{H}")
                    else: time.sleep(1); continue
                ret, frame = self.cap.read()
                if ret:
                    with frame_lock: current_frame = frame
                    cam_online = True
                else:
                    print("[Camera] read failed, reopening...")
                    self.cap.release(); self.cap = None; cam_online = False; time.sleep(1)
            except Exception as e:
                print(f"[Camera] error: {e}"); time.sleep(1)
    def stop(self):
        self.running = False
        if self.cap: self.cap.release()

class HWRecorder:
    def __init__(self):
        self.pipeline = None; self.appsrc = None; self.loop = None
        self.thread = None; self.fc = 0; self.start_ts = 0; self.active = False
        self.filepath = None; self._stop_req = False
    def path(self):
        return os.path.join(REC_DIR, f"record_{time.strftime('%Y%m%d_%H%M%S')}.mp4")
    def start(self):
        if self.active: return False
        self.active = True; self.fc = 0; self._stop_req = False
        self.thread = threading.Thread(target=self._run, daemon=True); self.thread.start()
        return True
    def _run(self):
        global current_frame
        self.filepath = self.path()
        ps = (f"appsrc name=src is-live=true format=time caps=video/x-raw,format=BGR,width={W},height={H},framerate={FPS}/1 "
              "! videoconvert ! video/x-raw,format=NV12 ! mpph264enc ! h264parse ! qtmux ! "
              f"filesink location={self.filepath}")
        self.pipeline = Gst.parse_launch(ps)
        self.appsrc = self.pipeline.get_by_name("src"); self.appsrc.set_property("block", True)
        self.loop = GLib.MainLoop()
        bus = self.pipeline.get_bus(); bus.add_signal_watch()
        def on_error(b, m): err, _ = m.parse_error(); print(f"[Rec] ERROR: {err}"); self.loop.quit()
        def on_eos(b, m): self.loop.quit()
        bus.connect("message::error", on_error); bus.connect("message::eos", on_eos)
        self.pipeline.set_state(Gst.State.PLAYING); time.sleep(0.5)
        self.start_ts = time.time()
        print(f"[Rec] started → {self.filepath}")
        while self.active and not self._stop_req:
            with frame_lock: f = current_frame
            if f is None: time.sleep(0.01); continue
            buf = Gst.Buffer.new_wrapped(f.tobytes())
            buf.pts = buf.dts = Gst.util_uint64_scale(self.fc, Gst.SECOND, FPS)
            buf.duration = Gst.util_uint64_scale(1, Gst.SECOND, FPS)
            if self.appsrc.emit("push-buffer", buf) != Gst.FlowReturn.OK: break
            self.fc += 1
        self.appsrc.emit("end-of-stream")
        self.loop.run()
        self.pipeline.set_state(Gst.State.NULL)
        self.active = False
        elapsed = time.time() - self.start_ts
        sz = os.path.getsize(self.filepath) if os.path.exists(self.filepath) else 0
        print(f"[Rec] DONE → {self.filepath}  ({sz/1024:.0f}KB, {self.fc}帧, {self.fc/elapsed:.1f}FPS)")
    def stop(self):
        if not self.active: return
        self._stop_req = True
        if self.thread: self.thread.join(timeout=10)

app = Flask(__name__)

def gen_stream():
    while True:
        try:
            with frame_lock: f = current_frame
            if f is None: time.sleep(0.5); continue
            _, jpg = cv2.imencode(".jpg", f, [cv2.IMWRITE_JPEG_QUALITY, JPEG_Q])
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpg.tobytes() + b"\r\n"
            time.sleep(1 / FPS)
        except GeneratorExit: break

@app.route("/stream")
def stream():
    return Response(gen_stream(), mimetype="multipart/x-mixed-replace; boundary=frame",
                    headers={"Cache-Control": "no-cache"})

@app.route("/status")
def status():
    files = sorted(os.listdir(REC_DIR), reverse=True)[:30]
    fl = []
    for f in files:
        fp = os.path.join(REC_DIR, f)
        try: sz = os.path.getsize(fp); mt = os.path.getmtime(fp); fl.append({"name": f, "size": sz, "time": mt})
        except: pass
    return jsonify({"cam_online": cam_online, "recording": recording, "resolution": f"{W}x{H}", "fps": FPS, "files": fl})

@app.route("/record/start", methods=["POST"])
def rec_start():
    global recording, recorder
    if recording: return jsonify({"ok": False})
    recorder = HWRecorder()
    if recorder.start(): recording = True; return jsonify({"ok": True})
    return jsonify({"ok": False})

@app.route("/record/stop", methods=["POST"])
def rec_stop():
    global recording, recorder
    if not recording: return jsonify({"ok": False})
    recorder.stop()
    fc = recorder.fc; fp = recorder.filepath or ""
    sz = os.path.getsize(fp) if fp and os.path.exists(fp) else 0
    recording = False
    return jsonify({"ok": True, "frames": fc, "file": os.path.basename(fp) if fp else "", "size": sz})

@app.route("/download/<filename>")
def download(filename):
    fp = os.path.join(REC_DIR, filename)
    if not os.path.exists(fp): abort(404)
    return send_file(fp, as_attachment=True, download_name=filename)

@app.route("/")
def index():
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>RKCamRecord3 — 相机控制台</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,sans-serif;background:#0f0f0f;color:#eee;min-height:100vh}
.container{max-width:1100px;margin:0 auto;padding:16px}
header{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:8px}
h1{font-size:20px;background:linear-gradient(135deg,#667eea,#764ba2);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.status-badge{font-size:13px;padding:4px 12px;border-radius:20px;display:inline-flex;align-items:center;gap:6px}
.online{background:#1a3a1a;color:#4ade80;border:1px solid #4ade8044}
.offline{background:#3a1a1a;color:#f87171;border:1px solid #f8717144}
.recording-yes{background:#3a1a1a;color:#f87171;border:1px solid #f8717144;animation:pulse 1.5s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.6}}
.stream-box{background:#1a1a2e;border-radius:12px;overflow:hidden;border:1px solid #2a2a3e;margin-bottom:16px}
.stream-box img{width:100%;display:block}
.controls{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px}
.btn{padding:10px 24px;border:none;border-radius:8px;font-size:15px;font-weight:600;cursor:pointer;transition:.2s;display:flex;align-items:center;gap:6px}
.btn:active{transform:scale(.96)}
.btn-rec{background:#dc2626;color:#fff}.btn-rec:hover{background:#b91c1c}
.btn-stop{background:#6366f1;color:#fff}.btn-stop:hover{background:#4f46e5}
.btn:disabled{opacity:.4;cursor:not-allowed}
.info-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:16px}
.info-card{background:#1a1a2e;border-radius:8px;padding:12px;border:1px solid #2a2a3e;text-align:center}
.info-card .label{font-size:11px;color:#888;text-transform:uppercase}
.info-card .value{font-size:20px;font-weight:700;margin-top:4px}
.files-box{background:#1a1a2e;border-radius:8px;border:1px solid #2a2a3e;padding:12px}
.files-box h3{font-size:14px;color:#888;margin-bottom:8px}
.file-item{display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid #2a2a3e;font-size:13px}
.file-item:last-child{border:none}
.file-item .fname{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.file-item .fsize{color:#888;margin:0 12px;white-space:nowrap}
.file-item .fdl{color:#60a5fa;text-decoration:none;padding:4px 10px;border-radius:4px;background:#1e3a5f;font-size:12px}
.file-item .fdl:hover{background:#2563eb}
.rec-dot{width:8px;height:8px;border-radius:50%;background:#dc2626;display:inline-block}
.rec-dot.active{animation:pulse 1s infinite}
.toast{position:fixed;top:20px;right:20px;background:#1a3a1a;border:1px solid #4ade8044;color:#4ade80;padding:16px 20px;border-radius:12px;max-width:360px;z-index:999;box-shadow:0 8px 32px rgba(0,0,0,.5);transform:translateX(120%);transition:transform .3s ease}
.toast.show{transform:translateX(0)}
.toast .tt{font-weight:700;font-size:15px;margin-bottom:4px}
.toast .ts{font-size:12px;color:#aaa}
</style></head>
<body>
<div id="toast" class="toast"><div class="tt">✅ 录像完成</div><div class="ts" id="toastMsg"></div></div>
<div class="container">
  <header><h1>📷 RKCamRecord3</h1>
    <div style="display:flex;gap:8px;flex-wrap:wrap">
      <span id="camBadge" class="status-badge offline">🔴 相机离线</span>
      <span id="recBadge" class="status-badge offline">⏹ 未录像</span>
    </div>
  </header>
  <div class="stream-box"><img src="/stream" alt="实时画面"></div>
  <div class="controls">
    <button class="btn btn-rec" id="btnStart" onclick="startRec()">🎬 开始录像</button>
    <button class="btn btn-stop" id="btnStop" onclick="stopRec()" disabled>⏹ 停止录像</button>
  </div>
  <div class="info-grid">
    <div class="info-card"><div class="label">分辨率</div><div class="value">1920×1080</div></div>
    <div class="info-card"><div class="label">帧率</div><div class="value">24 FPS</div></div>
    <div class="info-card"><div class="label">编码</div><div class="value">H.264 HW</div></div>
    <div class="info-card"><div class="label">录像时长</div><div class="value" id="recTime">00:00</div></div>
  </div>
  <div class="files-box">
    <h3>📁 已录文件 <span style="color:#666;font-weight:400;font-size:12px">（点击下载到电脑）</span></h3>
    <div id="fileList">加载中...</div>
  </div>
</div>
<script>
let recStartTime=null,recTimer=null
function showToast(msg,dur){document.getElementById('toastMsg').textContent=msg;document.getElementById('toast').classList.add('show');setTimeout(()=>document.getElementById('toast').classList.remove('show'),dur||5000)}
function fmtSize(b){if(!b)return'0B';const u=['B','KB','MB','GB'];let i=0;while(b>=1024&&i<3){b/=1024;i++}return(i<2?Math.round(b):b.toFixed(1))+u[i]}
function updateStatus(){fetch('/status').then(r=>r.json()).then(d=>{
document.getElementById('camBadge').className='status-badge '+(d.cam_online?'online':'offline')
document.getElementById('camBadge').innerHTML=d.cam_online?'🟢 相机在线':'🔴 相机离线'
const r=d.recording
document.getElementById('recBadge').className='status-badge '+(r?'recording-yes':'offline')
document.getElementById('recBadge').innerHTML=r?'<span class="rec-dot active"></span> 录像中':'⏹ 未录像'
document.getElementById('btnStart').disabled=r;document.getElementById('btnStop').disabled=!r
if(!r&&recTimer){clearInterval(recTimer);recTimer=null}
if(r&&!recTimer){recStartTime=Date.now();recTimer=setInterval(()=>{const s=Math.floor((Date.now()-recStartTime)/1000);document.getElementById('recTime').textContent=String(Math.floor(s/60)).padStart(2,'0')+':'+String(s%60).padStart(2,'0')},1000)}
if(!r)document.getElementById('recTime').textContent='00:00'
if(d.files&&d.files.length){document.getElementById('fileList').innerHTML=d.files.map(f=>'<div class="file-item"><span class="fname">'+f.name+'</span><span class="fsize">'+fmtSize(f.size)+'</span><a class="fdl" href="/download/'+f.name+'" download>⬇ 下载</a></div>').join('')}else{document.getElementById('fileList').innerHTML='<div style="color:#666;font-size:13px">暂无录像文件</div>'}
}).catch(()=>{})}
function startRec(){fetch('/record/start',{method:'POST'}).then(r=>r.json()).then(d=>{if(d.ok)updateStatus()})}
function stopRec(){fetch('/record/stop',{method:'POST'}).then(r=>r.json()).then(d=>{if(d.ok){updateStatus();const msg=d.file+' ('+fmtSize(d.size)+', '+d.frames+'帧)';showToast(msg,6000);setTimeout(updateStatus,500)}})}
updateStatus();setInterval(updateStatus,3000)
</script></body></html>"""

if __name__ == "__main__":
    print("="*50)
    print("  RKCamRecord3 v8 — 稳定录像 + 下载")
    print("="*50)
    cam = CameraWorker(); cam.start(); time.sleep(1)
    print(f"  http://0.0.0.0:{PORT}/")
    print(f"  📁 {REC_DIR}/")
    app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True)
