# RKCamRecord3 — RK3576 相机推流 + 硬件编码录像

基于 Rockchip RK3576S + IMX415 的相机服务，支持 MJPEG 推流和 **MPP 硬件 H.264 编码**录像。

## 硬件

| 组件 | 型号 |
|------|------|
| 主控 | Rockchip RK3576S (Cortex-A72×4 + A53×4) |
| 相机 | Sony IMX415 (MIPI CSI, 4K) → /dev/video11 |
| 编码 | Rockchip MPP (mpph264enc) 硬件 H.264 |
| 存储 | 29GB eMMC，录像目录 `/home/cat/recordings/` |

## 架构

```
┌─────────────┐    ┌──────────┐    ┌───────────┐
│  OpenCV     │───▶│ GStreamer│───▶│ MP4 File  │
│  Capture    │    │ appsrc   │    │ (HW Enc)  │
└──────┬──────┘    └──────────┘    └───────────┘
       │
       ▼
┌──────────────────┐
│ Flask Web UI     │
│ :5000/           │
│ - 实时画面       │
│ - 开始/停止录像  │
│ - 文件下载       │
└──────────────────┘
```

## 快速开始

板子通电后，打开浏览器访问：

```
http://192.168.55.32:5000/
```

（IP 以实际为准）

## 文件说明

| 文件 | 说明 |
|------|------|
| `board_cam_record.py` | 主程序（Flask + GStreamer MPP 编码 + Web UI） |
| `start_cam.sh` | 一键启动脚本 |
| `setup_cam_v2.sh` | 相机管线配置（vblank 修复） |
| `cam-record.service` | systemd 自启动服务 |

## 安装到板子

```bash
# 1. 配置相机管线
v4l2-ctl -d /dev/v4l-subdev2 --set-ctrl vertical_blanking=200
v4l2-ctl -d /dev/video11 --set-fmt-video=width=1920,height=1080,pixelformat=NV12

# 2. 运行
python3 board_cam_record.py

# 3. 开机自启（推荐）
sudo cp cam-record.service /etc/systemd/system/
sudo systemctl enable cam-record.service
sudo systemctl start cam-record.service
```

## API

| 路由 | 方法 | 说明 |
|------|------|------|
| `/` | GET | Web UI 控制台 |
| `/stream` | GET | MJPEG 实时推流 |
| `/status` | GET | JSON 状态（相机、录像状态、文件列表） |
| `/record/start` | POST | 开始录像（硬件 H.264 编码） |
| `/record/stop` | POST | 停止录像，返回文件信息 |
| `/download/&lt;filename&gt;` | GET | 下载录像文件 |

## 录像效果

| 指标 | 数值 |
|------|------|
| 分辨率 | 1920×1080 |
| 帧率 | 24 FPS |
| 编码 | H.264 High Profile (硬件 MPP) |
| 码率 | ~6 Mbps |
| CPU 占用 | ~10-20%（硬件编码） |

## 排坑记录

1. **ISP 启动失败** — `start pipeline failed -22`，传感器 vblank 默认 58 行太短（859µs < 1000µs），调高到 200 解决
2. **rkaiq_3A 阻塞** — 3A 服务启动时会持有 ISP 管线，配置格式后再启动可解决
3. **MP4 文件损坏** — 使用 `qtmux` 替代 `mp4mux`，并确保 EOS 完全传播后才关闭管线
