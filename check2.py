import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import paramiko

s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect('192.168.55.18', username='cat', password='temppwd', timeout=10)

# 检查进程
i,o,e = s.exec_command("ps aux | grep -E 'board_cam|watchdog' | grep -v grep")
procs = o.read().decode().strip()
print('=== 进程 ===')
print(procs if procs else '无')

# 检查端口
i2,o2,e2 = s.exec_command('ss -tlnp | grep 5000 || echo "no port 5000"')
print('=== 端口 ===')
print(o2.read().decode().strip())

# 日志末尾
i3,o3,e3 = s.exec_command('tail -10 /home/cat/cam_server.log')
print('=== 日志 ===')
print(o3.read().decode().strip())

s.close()
