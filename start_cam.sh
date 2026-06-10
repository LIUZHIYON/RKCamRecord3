#!/bin/bash
# ===== RK3576 相机服务 — 一键启动 =====
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG="$SCRIPT_DIR/cam_server.log"

echo "========================================"
echo "  RKCamRecord3 — One Click Start"
echo "========================================"

# 1. 配置相机格式
echo "[1/3] 配置相机管线..."
v4l2-ctl -d /dev/v4l-subdev2 --set-ctrl vertical_blanking=200 2>/dev/null
v4l2-ctl -d /dev/video11 --set-fmt-video=width=1920,height=1080,pixelformat=NV12 > /dev/null 2>&1

# 2. 停止旧服务
echo "[2/3] 启动推流+录像服务..."
pkill -f "board_cam_record" 2>/dev/null || true
sleep 1

# 3. 启动新服务
cd "$SCRIPT_DIR"
nohup python3 "$SCRIPT_DIR/board_cam_record.py" > "$LOG" 2>&1 &
sleep 2

# 4. 验证
IP=$(hostname -I | awk '{print $1}')
echo "[3/3] 服务已启动！"
echo ""
echo "  📹 推流:  http://$IP:5000/stream"
echo "  📊 状态:  http://$IP:5000/status"
echo "  💾 录像:  curl -X POST http://$IP:5000/record/start"
echo "  ⏹ 停止:  curl -X POST http://$IP:5000/record/stop"
echo "  📁 文件:  $SCRIPT_DIR/recordings/"
echo ""
echo "  服务PID: $(pgrep -f board_cam_record)"
echo "  日志: $LOG"
echo "========================================"
