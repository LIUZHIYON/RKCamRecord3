import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import paramiko

s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect('192.168.55.18', username='cat', password='temppwd', timeout=10)

def run(cmd):
    i,o,e = s.exec_command(cmd)
    return o.read().decode(errors='replace') + e.read().decode(errors='replace')

print("=== media-ctl 管线 ===")
print(run("media-ctl -d /dev/media0 -p 2>&1 | head -30"))
print("---")
print(run("media-ctl -d /dev/media1 -p 2>&1 | head -50"))

print("\n=== v4l2-ctl 信息 ===")
print(run("v4l2-ctl -d /dev/video11 --all 2>&1 | head -20"))

print("\n=== rkisp 相关 ===")
print(run("ls /sys/class/video4linux/video11/name 2>&1 && cat /sys/class/video4linux/video11/name"))

print("\n=== 尝试设置格式 ===")
print(run("v4l2-ctl -d /dev/video11 --set-fmt-video=width=1280,height=720,pixelformat=NV12 2>&1"))
print(run("v4l2-ctl -d /dev/video11 --get-fmt-video 2>&1"))

print("\n=== 测试读一帧 ===")
print(run("timeout 3 v4l2-ctl -d /dev/video11 --stream-mmap --stream-to=/tmp/test.raw --stream-count=1 2>&1 || echo timeout"))

s.close()
