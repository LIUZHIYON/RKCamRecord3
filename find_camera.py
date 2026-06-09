import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.55.18', username='cat', password='temppwd', timeout=10)

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode(errors='replace') + stderr.read().decode(errors='replace')

print("=== 查看所有 video 设备 ===")
print(run("ls -la /dev/video*"))

print("\n=== media 设备 ===")
print(run("ls -la /dev/media*"))

print("\n=== v4l2 信息 ===")
for i in range(0, 22):
    out = run(f"v4l2-ctl -d /dev/video{i} --info 2>&1 | head -5")
    if "not a V4L2" not in out and out.strip():
        print(f"\n--- /dev/video{i} ---")
        print(out.strip())

print("\n=== 查看 v4l2 设备列表 ===")
print(run("v4l2-ctl --list-devices 2>&1"))

print("\n=== 查看 camera symlink ===")
print(run("ls -la /dev/v4l/ 2>&1"))
print(run("find /dev -name '*camera*' -o -name '*cam*' 2>/dev/null"))

print("\n=== 测试打开摄像头 (0, 11) ===")
print(run("python3 -c \"import cv2; cap=cv2.VideoCapture(11); print('video11:', cap.isOpened()); cap.release(); cap=cv2.VideoCapture(0); print('video0:', cap.isOpened()); cap.release()\" 2>&1"))

print("\n=== dmesg 摄像头信息 ===")
print(run("dmesg | grep -i camera | tail -10 2>&1"))
print(run("dmesg | grep -i 'video\|usb' | tail -10 2>&1"))

ssh.close()
