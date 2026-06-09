@echo off
chcp 65001 >nul
title RKCamRecord3 — PC端控制面板

echo ============================================
echo   🎥 RKCamRecord3 启动中...
echo ============================================
echo.
echo 📌 请确保:
echo   1. 板子 (192.168.55.18) 已通电联网
echo   2. 板子上已运行 board_cam_server.py
echo      (SSH连接后: python3 board_cam_server.py ^&)
echo.
echo ============================================
echo.

pip install -r requirements.txt -q

python pc_server.py

pause
