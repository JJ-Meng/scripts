from signal import SIGKILL
import os
import subprocess
cmd='arping 127.0.0.1'
cmd_list=cmd.split(" ")
try:
    #user=1000
    subp = subprocess.Popen(cmd_list,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    pid=subp.pid
    temp={cmd:pid}
    #cmd_pid.update(temp)
    #print(f"cmd:{cmd} pid is {pid}")
    outs, errs=subp.communicate(timeout=3)
except subprocess.TimeoutExpired:
    # subp.kill()
    os.kill(pid,SIGKILL)
    print(f'!timeout! cmd: {cmd}')
    outs, errs=subp.communicate()
except UnicodeDecodeError:
    # subp.kill()
    print(f"some encoding fault!")
except FileNotFoundError:
    # subp.kill()
    print(f"file not found!")
