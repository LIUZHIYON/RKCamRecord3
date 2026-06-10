#!/bin/bash
# RK3576 IMX415 相机管线配置 v2
set -e

echo "=== 配置 ISP 管线 (1920x1080) ==="

# 1. 设置 sensor format (IMX415) — 提高 vblank 给 ISP 足够时间
echo "[1] Sensor format"
v4l2-ctl -d /dev/v4l-subdev2 --set-ctrl vertical_blanking=200 2>/dev/null || true

# 2. 设置 v4l2 设备格式
echo "[2] Video device format"
v4l2-ctl -d /dev/video11 --set-fmt-video=width=1920,height=1080,pixelformat=NV12 2>&1

# 3. 验证
echo "[3] Verify"
v4l2-ctl -d /dev/video11 --get-fmt-video 2>&1 | grep -E "Width|Pixel"
echo "=== Done ==="
