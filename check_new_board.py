import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import paramiko

s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect('192.168.55.32', username='cat', password='temppwd', timeout=10)

def run(cmd):
    i,o,e = s.exec_command(cmd + ' 2>&1')
    return o.read().decode(errors='replace')

print("=== 设备 ===")
print(run("ls -la /dev/video-camera0 2>&1; ls -la /dev/video* 2>&1 | head -5"))

print("=== media0 ===")
print(run("media-ctl -d /dev/media0 -p 2>&1 | grep -E 'pad|ENABLED|fmt:|imx|entity'"))

print("=== media1 ===")
print(run("media-ctl -d /dev/media1 -p 2>&1 | grep -E 'pad|ENABLED|fmt:|imx|entity'"))

print("=== video0 fmt ===")
print(run("v4l2-ctl -d /dev/video0 --get-fmt-video 2>&1"))

print("=== video11 fmt ===")
print(run("v4l2-ctl -d /dev/video11 --get-fmt-video 2>&1"))

s.close()
