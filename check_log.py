import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import paramiko

s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect('192.168.55.18', username='cat', password='temppwd', timeout=10)

i,o,e = s.exec_command('cat /home/cat/cam_server.log 2>&1')
print(o.read().decode(errors='replace')[-1000:])

i2,o2,e2 = s.exec_command("ps aux | grep board_cam | grep -v grep")
print(f"\nProcess: {o2.read().decode().strip() or 'dead'}")

s.close()
