# RKCamRecord3 — RK3576 相机推流 + 硬件编码录像

基于 Rockchip RK3576S + IMX415 的相机服务。**推流 + 硬件 H.264 编码录像 + 文件下载，一个页面全搞定。**

## 🚀 一键启动

### 在板子上部署
```bash
# 克隆到板子
git clone https://github.com/LIUZHIYON/RKCamRecord3.git /home/cat/RKCamRecord3
cd /home/cat/RKCamRecord3

# 一键启动
bash start_cam.sh
```

### 电脑浏览器打开
```
http://192.168.1.204:5000/
```
> 把 IP 换成板子实际的 IP 地址

### 开机自启（推荐）
```bash
sudo cp cam-record.service /etc/systemd/system/
sudo systemctl enable cam-record.service
sudo systemctl start cam-record.service
```
板子通电后自动运行，无需任何操作。

## 📋 Web 界面功能

| 功能 | 说明 |
|------|------|
| 📺 实时画面 | MJPEG 推流预览 |
| 🎬 开始/停止录像 | 一键控制，停止时弹窗提示文件名、大小、帧数 |
| ⬇️ 下载录像 | 文件列表点击「下载」直接保存到电脑 |
| 🔄 分辨率切换 | 下拉选择：1080p / 720p / 480p / 360p，实时生效 |

## 📁 项目文件

| 文件 | 说明 |
|------|------|
| `board_cam_record.py` | 主程序（Flask + OpenCV + GStreamer MPP 硬件编码 + Web UI） |
| `start_cam.sh` | 一键启动脚本 |
| `setup_cam_v2.sh` | 相机管线配置（修复 ISP vblank 问题） |
| `cam-record.service` | systemd 开机自启配置 |
| `requirements.txt` | Python 依赖 |

## 📡 API

| 路由 | 方法 | 说明 |
|------|------|------|
| `/` | GET | Web UI 控制台 |
| `/stream` | GET | MJPEG 实时推流 |
| `/status` | GET | JSON 状态（相机、录像、分辨率列表） |
| `/resolution/<名称>` | POST | 切换分辨率 |
| `/record/start` | POST | 开始录像 |
| `/record/stop` | POST | 停止录像 |
| `/download/<文件>` | GET | 下载录像文件 |

## 📊 录像规格

| 指标 | 1080p | 720p | 480p | 360p |
|------|-------|------|------|------|
| 分辨率 | 1920×1080 | 1280×720 | 640×480 | 480×360 |
| 帧率 | 24 FPS | 24 FPS | 24 FPS | 24 FPS |
| 编码 | H.264 HW | H.264 HW | H.264 HW | H.264 HW |
| 码率 | ~6 Mbps | ~3 Mbps | ~1 Mbps | ~500 Kbps |

## 🔧 常见问题

### 视频打不开
v8+ 已修复：使用 `qtmux` + 完整 EOS 等待机制，确保 MP4 文件有效。

### 相机离线
```bash
v4l2-ctl -d /dev/v4l-subdev2 --set-ctrl vertical_blanking=200
v4l2-ctl -d /dev/video11 --set-fmt-video=width=1920,height=1080,pixelformat=NV12
```

### ISP 启动失败
`start pipeline failed -22`：传感器默认 vblank=58 太短，调高到 200 即可。

### 网页断联 / IP 变了
板子重启后 IP 可能变化，重新访问新 IP 即可。
