# 🎥 RKCamRecord3 — 摄像头远程录制控制

电脑端通过 Web 浏览器控制 RK3576 板子上的摄像头，进行**实时预览、录制、管理**。

---

## 📋 项目结构

```
RKCamRecord3/
├── pc_server.py              # PC 端 Web 服务器（运行这个）
├── board_cam_server.py       # 板端摄像头服务器（传到板子上运行）
├── run_pc.bat                # 一键启动 PC 端
├── templates/
│   └── index.html            # Web 界面
├── static/
│   └── style.css             # 界面样式
├── recordings/               # 录制的视频文件
├── requirements.txt          # Python 依赖
└── README.md                 # 本文件
```

---

## 🚀 快速开始

### 1️⃣ 板子端 — 启动摄像头服务器

```bash
# 1. SSH 连接到 RK3576
ssh cat@192.168.55.18
# 密码: temppwd

# 2. 将 board_cam_server.py 传到板子（在电脑上执行）
scp board_cam_server.py cat@192.168.55.18:~/

# 3. 在板子上运行
ssh cat@192.168.55.18 "python3 ~/board_cam_server.py"
```

看到 `Stream 地址: http://0.0.0.0:5000/stream` 即可。

### 2️⃣ 电脑端 — 打开控制面板

```bash
# 双击 run_pc.bat，或在终端执行：
python pc_server.py
```

浏览器自动打开 `http://localhost:5001`

---

## 🎮 功能说明

| 功能 | 操作 |
|------|------|
| **实时预览** | 打开页面即自动显示摄像头画面 |
| **开始录制** | 点击「● 开始录制」，帧保存在电脑本地 |
| **暂停/恢复** | 录制中点击「⏸ 暂停」，可随时恢复 |
| **停止录制** | 点击「■ 停止」，自动保存为 MP4 文件 |
| **文件名** | 录制前可自定义文件名，留空自动命名 |
| **下载文件** | 在文件列表点击 ⬇️ 下载到电脑 |
| **重命名** | 点击 ✏️ 修改已保存的文件名 |
| **删除文件** | 点击 🗑️ 删除不需要的录制文件 |

---

## ⚙️ 配置说明

如需修改，编辑对应文件顶部：

| 参数 | 文件 | 默认值 |
|------|------|--------|
| 板子 IP | `pc_server.py` | `192.168.55.18` |
| 板子端口 | `pc_server.py` / `board_cam_server.py` | `5000` |
| PC 端口 | `pc_server.py` | `5001` |
| 摄像头设备 | `board_cam_server.py` | `/dev/video0, 11, 10, 21` |
| 分辨率 | `board_cam_server.py` | `1920x1080` |
| FPS | `board_cam_server.py` | `30` |

---

## 📦 依赖

- **PC 端:** Flask, OpenCV, requests, numpy
- **板端:** Flask, OpenCV, numpy
