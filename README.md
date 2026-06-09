# 🎥 RKCamRecord3 — 摄像头远程录制控制

> 在电脑上通过浏览器远程控制 **RK3576 板子** 上的 MIPI 摄像头（Sony IMX415），  
> 实现**实时预览、录制、暂停恢复、文件管理**一站式操作。

---

## 📋 项目结构

```
RKCamRecord3/
├── pc_server.py                # PC 端 Web 服务器（运行这个）
├── board_cam_server.py         # 板端摄像头服务器
├── watchdog.py                 # 板端守望脚本（自动保活）
├── redeploy.py                 # 一键部署+启动（PC→板子）
├── run_pc.bat                  # 双击启动 PC 端
├── templates/
│   └── index.html              # Web 界面
├── static/
│   └── style.css               # 界面样式
├── recordings/                 # 录制的视频文件
├── requirements.txt            # Python 依赖
└── README.md                   # 本文件
```

---

## 🚀 快速开始

### 1. 板子端 — 部署并启动摄像头服务

```bash
# 一键部署（上传 + 启动 + 守望）
python redeploy.py
```

或手动操作：

```bash
# SSH 连接板子
ssh cat@192.168.55.32

# 上传脚本（在电脑上执行）
scp board_cam_server.py cat@192.168.55.32:~/
scp watchdog.py cat@192.168.55.32:~/

# 在板子上启动
ssh cat@192.168.55.32 "setsid python3 ~/board_cam_server.py > ~/cam_server.log 2>&1 &"
ssh cat@192.168.55.32 "setsid python3 ~/watchdog.py > ~/watchdog.log 2>&1 &"
```

验证：`curl http://192.168.55.32:5000/status` 返回摄像头在线即可。

### 2. 电脑端 — 打开控制面板

```bash
# 双击 run_pc.bat，或：
python pc_server.py
```

浏览器打开 **http://localhost:5001**

---

## 🎮 功能介绍

| 功能 | 操作 |
|------|------|
| 📹 **实时预览** | 打开页面自动显示摄像头画面 |
| 🔴 **开始录制** | 点击「● 开始录制」，帧保存在电脑本地 |
| ⏸ **暂停/恢复** | 录制中可随时暂停和恢复 |
| ■ **停止录制** | 自动保存为 MP4，记录时长/帧数/分辨率 |
| ✏️ **重命名文件** | 在文件列表点击 ✏️ 修改文件名 |
| ⬇️ **下载文件** | 点击 ⬇️ 下载到电脑 |
| 🗑️ **删除文件** | 点击 🗑️ 删除不需要的录制文件 |
| 🛡️ **看门狗** | 板端守望脚本自动重启崩溃的服务 |

> 录制在 PC 端完成，不占用板子存储空间。

---

## ⚙️ 配置参数

编辑对应文件顶部即可修改：

| 参数 | 所在文件 | 默认值 |
|------|---------|--------|
| 板子 IP | `pc_server.py` | `192.168.55.32` |
| 板子端口 | `board_cam_server.py` / `pc_server.py` | `5000` |
| PC 端口 | `pc_server.py` | `5001` |
| 摄像头设备 | `board_cam_server.py` | `/dev/video11` (rkisp_mainpath) |
| 分辨率 | `board_cam_server.py` | `1920×1080` |
| 帧率限制 | `board_cam_server.py` | `24 fps` |
| JPEG 画质 | `board_cam_server.py` | `75` |

---

## 🏗️ 硬件架构

```
Sony IMX415 (MIPI CSI)
       ↓
rkisp (ISP) — 硬件去马赛克、AWB、缩放
       ↓
rkisp_mainpath (/dev/video11) — NV12 YUV 视频
       ↓
board_cam_server.py — MJPEG 流 (HTTP)
       ↓
PC Web 界面 — 预览 / 录制 / 管理
```

摄像头通过 MIPI-CSI 接口连接，走 Rockchip ISP 管线，输出 NV12 格式。  
板端服务器用 OpenCV 读取并编码为 MJPEG，PC 端通过 HTTP 拉流。

---

## 📦 依赖安装

### PC 端

```bash
pip install flask opencv-python requests numpy paramiko
```

### 板端 (RK3576, Debian)

```bash
pip3 install flask opencv-python numpy
```

---

## 📝 注意

- 录制文件保存在电脑端 `recordings/` 目录，板子不存文件
- `redeploy.py` 依赖 `paramiko`，可一键部署到板子
- 板端 `watchdog.py` 每 5 秒检测一次进程，崩溃自动重启
- `fix_media0.py` 可在 ISP 管线断裂时重新配置（通常无需使用）
