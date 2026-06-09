import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import paramiko

s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect('192.168.55.18', username='cat', password='temppwd', timeout=10)

def run(cmd):
    i,o,e = s.exec_command(cmd + ' 2>&1')
    return o.read().decode(errors='replace')

print("== 1. 停服务 ==")
run("pkill -f board_cam_server.py 2>/dev/null; pkill -f watchdog.py 2>/dev/null")
time.sleep(2)

print("== 2. 查看摄像头相关内核模块 ==")
print(run("lsmod | grep -iE 'imx|isp|cif|mipi|cam' 2>&1"))
print(run("find /lib/modules -name '*imx*' -o -name '*rkisp*' -o -name '*rkcif*' 2>/dev/null"))

print("== 3. 查看 sensor 子设备详情 ==")
print(run("media-ctl -d /dev/media1 -e 'm00_b_imx415 5-001a' -p 2>&1 | head -20"))

print("== 4. 查看 imx415 驱动参数 ==")
print(run("find /sys/module -name '*imx*' -type d 2>/dev/null"))

print("== 5. 检查 sysfs 中 sensor 的信息 ==")
print(run("find /sys -name '*imx415*' -o -path '*5-001a*' 2>/dev/null"))

s.close()
