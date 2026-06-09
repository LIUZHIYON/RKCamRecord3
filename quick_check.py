import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import paramiko

s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect('192.168.55.18', username='cat', password='temppwd', timeout=10)

i,o,e = s.exec_command('curl -s http://localhost:5000/status 2>&1 || echo empty')
print('Status:', o.read().decode().strip())

i2,o2,e2 = s.exec_command('tail -3 /home/cat/cam_server.log')
print('Log:', o2.read().decode().strip())

s.close()
