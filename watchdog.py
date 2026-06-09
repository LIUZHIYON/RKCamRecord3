# board_cam_server.py 守望脚本
# 在板子上运行： nohup python3 watchdog.py &
# 会自动检测 board_cam_server 进程，挂了就重启

import os, time, sys, subprocess

SCRIPT = "/home/cat/board_cam_server.py"
LOG = "/home/cat/cam_server.log"
PIDFILE = "/tmp/board_cam.pid"

def is_running():
    """检查进程是否存在"""
    try:
        r = subprocess.run(
            ["pgrep", "-f", "board_cam_server.py"],
            capture_output=True, text=True, timeout=3
        )
        return len(r.stdout.strip().splitlines()) > 0
    except:
        return False

def start():
    """启动服务"""
    with open(LOG, "a") as log:
        subprocess.Popen(
            ["python3", SCRIPT],
            stdout=log, stderr=subprocess.STDOUT,
            start_new_session=True  # 脱离SSH
        )
    return True

if __name__ == "__main__":
    print(f"[Watchdog] started, checking {SCRIPT}")
    while True:
        if not is_running():
            print(f"[Watchdog] process dead, restarting...")
            with open(LOG, "a") as log:
                log.write(f"\n[Watchdog] restarting at {time.ctime()}\n")
            start()
        time.sleep(5)
