import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import paramiko

s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect('192.168.55.18', username='cat', password='temppwd', timeout=10)

def run(cmd):
    i,o,e = s.exec_command(cmd + ' 2>&1')
    return o.read().decode(errors='replace')

print("== Kill servers ==")
run("pkill -f board_cam_server.py 2>/dev/null; pkill -f watchdog.py 2>/dev/null")
time.sleep(2)

print("== Unbind IMX415 ==")
run("echo 5-001a > /sys/bus/i2c/drivers/imx415/unbind")
time.sleep(3)

print("== Check sensor gone ==")
print(run("media-ctl -d /dev/media1 -p"))

print("== Re-bind IMX415 ==")
run("echo 5-001a > /sys/bus/i2c/drivers/imx415/bind")
time.sleep(4)

print("== Check sensor back ==")
print(run("media-ctl -d /dev/media1 -p | head -50"))

s.close()
