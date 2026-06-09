import sys, os, time
sys.stdout.reconfigure(encoding='utf-8')
import paramiko

HOST = "192.168.55.18"
USER = "cat"
PASS = "temppwd"
LOCAL = r"C:\Users\29503\Desktop\RKCamRecord3\board_cam_server.py"
REMOTE = "/home/cat/board_cam_server.py"

print("=" * 50)
print("  部署板端服务器...")
print("=" * 50)

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS, timeout=10)
    print("[1] SSH 连接成功")

    sftp = ssh.open_sftp()
    sftp.put(LOCAL, REMOTE)
    sftp.close()
    print("[2] 上传完毕")

    print("[3] 重启服务...")
    stdin, stdout, stderr = ssh.exec_command("pkill -f board_cam_server.py 2>/dev/null; sleep 1; nohup python3 /home/cat/board_cam_server.py > /home/cat/cam_server.log 2>&1 &")
    stdout.channel.recv_exit_status()
    time.sleep(4)

    print("[4] 验证状态...")
    stdin2, stdout2, stderr2 = ssh.exec_command("curl -s http://localhost:5000/status")
    status = stdout2.read().decode().strip()
    if status:
        print("  状态:", status)
    else:
        print("  状态为空，查看日志...")
        stdin3, stdout3, stderr3 = ssh.exec_command("tail -5 /home/cat/cam_server.log")
        print("  日志:", stdout3.read().decode().strip())

    ssh.close()
    print("[5] 完成")

except Exception as e:
    print("错误:", e)
    sys.exit(1)
