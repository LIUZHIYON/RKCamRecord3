import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import paramiko

s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect('192.168.55.18', username='cat', password='temppwd', timeout=10)

def run(cmd):
    i,o,e = s.exec_command(cmd + ' 2>&1')
    return o.read().decode(errors='replace')

print("=== video0 ===")
print(run("v4l2-ctl -d /dev/video0 --get-fmt-video 2>&1"))

print("=== video4 ===")
print(run("v4l2-ctl -d /dev/video4 --get-fmt-video 2>&1"))

print("=== video11 ===")
print(run("v4l2-ctl -d /dev/video11 --get-fmt-video 2>&1"))

s.close()
