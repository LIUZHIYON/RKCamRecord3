# RKCamRecord3 — RK3576 相机推流 + 硬件编码录像

基于 Rockchip RK3576S + IMX415 的相机服务。**推流 + 硬件 H.264 编码录像 + 文件下载，一个页面全搞定。**

## 🚀 快速启动

### 在板子上（一键启动）

```bash
# 克隆到板子
git clone https://github.com/LIUZHIYON/RKCamRecord3.git /home/cat/RKCamRecord3
cd /home/cat/RKCamRecord3

# 运行
bash start_cam.sh
```

### 在电脑上（浏览器打开）

```
http://192.168.55.32:5000/
```

> IP 以板子实际 IP 为准。

### 开机自启（推荐）

```bash
sudo cp cam-record.service /etc/systemd/system/
sudo systemctl enable cam-record.service
sudo systemctl start cam-record.service
```

板子通电后自动运行，无需任何操作。

---

## 📋 Web 界面

打开 `http://192.168.55.32:5000/` 后：

| 功能 | 操作 |
|------|------|
| 📺 实时画面 | 页面自动显示 MJPEG 推流 |
| 🎬 开始录像 | 点击「开始录像」按钮 |
| ⏹ 停止录像 | 点击「停止录像」按钮，自动弹出完成通知 |
| ⬇ 下载视频 | 在文件列表中点击「下载」，保存到电脑 |

录像文件保存在板子 `/home/cat/recordings/` 目录下。

## 🏗 项目文件

| 文件 | 说明 |
|------|------|
| `board_cam_record.py` | 主程序（Flask + OpenCV + GStreamer MPP 编码 + Web UI） |
| `start_cam.sh` | **一键启动脚本**（配置相机 → 启动服务） |
| `setup_cam_v2.sh` | 相机管线配置（修复 ISP vblank 问题） |
| `cam-record.service` | systemd 开机自启配置 |
| `requirements.txt` | Python 依赖 |

## 🛠 手动部署

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置相机格式
v4l2-ctl -d /dev/v4l-subdev2 --set-ctrl vertical_blanking=200
v4l2-ctl -d /dev/video11 --set-fmt-video=width=1920,height=1080,pixelformat=NV12

# 3. 启动服务
python3 board_cam_record.py
```

## 📡 API

| 路由 | 方法 | 说明 |
|------|------|------|
| `/` | GET | Web UI 控制台 |
| `/stream` | GET | MJPEG 实时推流 |
| `/status` | GET | JSON 状态 |
| `/record/start` | POST | 开始录像 |
| `/record/stop` | POST | 停止录像 |
| `/download/<文件>` | GET | 下载录像文件 |

## 📊 录像规格

| 指标 | 数值 |
|------|------|
| 分辨率 | 1920×1080（1080p） |
| 帧率 | 24 FPS |
| 编码 | H.264 High Profile（硬件 MPP） |
| 码率 | ~6 Mbps |
| CPU 占用 | ~10-20% |
| 文件大小 | 约 1MB / 秒 |

## 🔧 常见问题

### 视频打不开 / 文件损坏
v8 已修复：使用 `qtmux` 替代 `mp4mux`，并确保 EOS 完整传播后才关闭管线。

### 相机离线
```bash
# 重新配置
v4l2-ctl -d /dev/v4l-subdev2 --set-ctrl vertical_blanking=200
v4l2-ctl -d /dev/video11 --set-fmt-video=width=1920,height=1080,pixelformat=NV12
```

### ISP 启动失败
内核日志报 `start pipeline failed -22`：
- 传感器默认 vblank=58 太短（859µs < ISP 需要的 1000µs）
- 调高到 200 即可解决（`setup_cam_v2.sh` 已包含此修复）
