import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import paramiko

s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect('192.168.55.18', username='cat', password='temppwd', timeout=10)

def run(cmd):
    i,o,e = s.exec_command(cmd)
    return o.read().decode(errors='replace')

# 杀所有进程
run("pkill -f board_cam_server 2>/dev/null; pkill -f watchdog 2>/dev/null; pkill -f python3 2>/dev/null")
import time; time.sleep(2)

# 重新加载 ISP 驱动
print("=== 重新加载 ISP 驱动 ===")
print(run("modprobe -r rkisp_v10 2>&1 || true"))
print(run("modprobe -r rkcif_mipi_lvds3 2>&1 || true"))
time.sleep(1)
print(run("modprobe rkcif_mipi_lvds3 2>&1 || true"))
print(run("modprobe rkisp_v10 2>&1 || true"))
time.sleep(2)

# 检查摄像头设备
print("\n=== 设备恢复 ===")
print(run("ls -la /dev/video-camera0 2>&1"))
print(run("media-ctl -d /dev/media1 -p 2>&1 | grep -E 'pad0:|pad2:|ENABLED|fmt:' | head -10"))

s.close()
