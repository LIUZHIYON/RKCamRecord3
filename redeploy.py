import sys, os, time, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import paramiko

s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect('192.168.55.18', username='cat', password='temppwd', timeout=10)

sf = s.open_sftp()
sf.put(r'C:\Users\29503\Desktop\RKCamRecord3\board_cam_server.py', '/home/cat/board_cam_server.py')
sf.put(r'C:\Users\29503\Desktop\RKCamRecord3\watchdog.py', '/home/cat/watchdog.py')
sf.close()
print('upload ok')

s.exec_command('pkill -f board_cam_server.py 2>/dev/null')
s.exec_command('pkill -f watchdog.py 2>/dev/null')
time.sleep(2)

s.exec_command('setsid python3 /home/cat/board_cam_server.py > /home/cat/cam_server.log 2>&1 &')
time.sleep(3)

s.exec_command('setsid python3 /home/cat/watchdog.py > /home/cat/watchdog.log 2>&1 &')
time.sleep(2)

i,o,e = s.exec_command('curl -s http://localhost:5000/status')
print('Status:', o.read().decode().strip())

i2,o2,e2 = s.exec_command("ps aux | grep -E 'board_cam|watchdog' | grep -v grep")
print('Process:')
print(o2.read().decode().strip())

s.close()
print('done')
