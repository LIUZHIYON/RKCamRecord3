import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import paramiko

s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect('192.168.55.18', username='cat', password='temppwd', timeout=10)

def run(cmd):
    i,o,e = s.exec_command(cmd + ' 2>&1')
    return o.read().decode(errors='replace')

# 1. 停服务
run("pkill -f board_cam_server.py 2>/dev/null; pkill -f watchdog.py 2>/dev/null")
time.sleep(2)

# 2. 配置管线
print("== Link pipeline ==")
# 启用 rkcif-mipi-lvds3 -> rkisp-isp-subdev
print(run('media-ctl -d /dev/media1 -l "\'rkcif-mipi-lvds3\':0->\'rkisp-isp-subdev\':0[1]"'))
# 启用 rkisp-isp-subdev -> rkisp_mainpath
print(run('media-ctl -d /dev/media1 -l "\'rkisp-isp-subdev\':2->\'rkisp_mainpath\':0[1]"'))
# also enable rkisp-input-params
print(run('media-ctl -d /dev/media1 -l "\'rkisp-input-params\':0->\'rkisp-isp-subdev\':1[1]"'))
time.sleep(0.5)

# 3. 设 ISP 输出格式匹配 rkcif
print("\n== Set formats ==")
print(run('media-ctl -d /dev/media1 --set-v4l2 "\'rkisp-isp-subdev\':0[fmt:SBGGR10_1X10/640x480]"'))
print(run('media-ctl -d /dev/media1 --set-v4l2 "\'rkisp-isp-subdev\':0[crop:(0,0)/640x480]"'))
print(run('media-ctl -d /dev/media1 --set-v4l2 "\'rkisp-isp-subdev\':2[fmt:YUYV8_2X8/640x480]"'))

time.sleep(0.5)

# 4. 验证
print("\n== Verify ==")
print(run("media-ctl -d /dev/media1 -p | grep -E 'pad0|pad2|ENABLED|fmt:'"))

# 5. v4l2 test
print("\n== v4l2 test ==")
i,o,e = s.exec_command("timeout 3 v4l2-ctl -d /dev/video11 --stream-mmap --stream-count=1 --stream-to=/dev/null 2>&1")
print(o.read().decode(errors='replace'))
print(e.read().decode(errors='replace')[:200])

# 6. 启动服务
print("\n== Start server ==")
run("setsid python3 /home/cat/board_cam_server.py > /home/cat/cam_server.log 2>&1 &")
time.sleep(5)

i2,o2,e2 = s.exec_command("curl -s http://localhost:5000/status")
print("Status:", o2.read().decode().strip() or "(empty)")
i3,o3,e3 = s.exec_command("tail -5 /home/cat/cam_server.log")
print("Log:", o3.read().decode().strip())

s.close()
