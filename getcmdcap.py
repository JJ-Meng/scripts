import json
import subprocess
pid=16046
findpid='dmesg | grep current:'+str(pid)
subp = subprocess.run(findpid,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True,text=True)
out=subp.stdout.strip().split('\n')
print(out)
caps=[]
caps_unique=set()
result_dict={}
for o in out:
    if o=="":
        continue
    strcap=o.split(" ")[-1]
    cap=int(strcap)
    caps.append(cap)
    caps_unique.add(cap)
for cap in caps_unique:
    cap_num=caps.count(cap)
    res="check cap "+cap+" for "+str(cap_num)+" times"
    result={'cmd:':res}
    result_dict.update(result)
print(result_dict)

'''
with open('cmds_pid.txt','r')as f:
    cmd_pid={}
    content=f.read()
    cmd_pid=json.loads(content)
    for cmd in cmd_pid:
        pid=cmd_pid[cmd]
        findpid='dmesg | grep current:'+str(pid)
        subp = subprocess.run(findpid,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True,text=True)
        subp.stdout.strip().split('\n')
'''
