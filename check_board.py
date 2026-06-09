import paramiko, json, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.55.18', username='cat', password='temppwd', timeout=10)

print("=== 板端状态 ===")
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:5000/status 2>&1 || echo "FAIL"')
print(stdout.read().decode().strip())

print("\n=== 进程 ===")
stdin, stdout, stderr = ssh.exec_command('ps aux | grep board_cam | grep -v grep')
print(stdout.read().decode().strip() or "未运行")

print("\n=== 日志 (末尾10行) ===")
stdin, stdout, stderr = ssh.exec_command('tail -10 /home/cat/cam_server.log 2>&1')
print(stdout.read().decode().strip())

print("\n=== 摄像头设备 ===")
stdin, stdout, stderr = ssh.exec_command('ls -la /dev/video* 2>&1')
print(stdout.read().decode().strip())

ssh.close()
