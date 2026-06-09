import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import paramiko

s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect('192.168.55.18', username='cat', password='temppwd', timeout=10)

def run(cmd):
    i,o,e = s.exec_command(cmd + ' 2>&1')
    return o.read().decode(errors='replace')

run("pkill -f board_cam_server.py 2>/dev/null; pkill -f watchdog.py 2>/dev/null")
time.sleep(2)

print("=== Enable IMX415 pipeline ===")
print(run('media-ctl -d /dev/media0 -l "\'m00_b_imx415 5-001a\':0->\'rockchip-csi2-dphy3\':0[1]"'))
time.sleep(0.3)
print(run('media-ctl -d /dev/media0 -l "\'rockchip-csi2-dphy3\':1->\'rockchip-mipi-csi2\':0[1]"'))
time.sleep(0.3)

print("=== Verify ===")
print(run("media-ctl -d /dev/media0 -p"))

print("\n=== Test video0 ===")
i,o,e = s.exec_command("timeout 3 v4l2-ctl -d /dev/video0 --stream-mmap --stream-count=1 --stream-to=/dev/null 2>&1")
result = o.read().decode(errors='replace')
err = e.read().decode(errors='replace')
print(result[:300])
print(err[:300] if err.strip() else "")

s.close()
