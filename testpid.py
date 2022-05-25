import subprocess
cmds=[#'addpart /dev/sda 0 0 0',
#'agetty 1 --reload',
'accton on'
#,'arp -d 182.61.200.7'
]
result_dict={}
for cmd in cmds:
    print(cmd)
    cmd_list=cmd.split(" ")
    #TODO create process group and kill process group afterwards 
    #proc = subprocess.Popen(args, ..., preexec_fn=os.setsid)   # 1
    #proc = subprocess.Popen(args, ..., start_new_session=True) # 2
    subp = subprocess.Popen(cmd_list,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
    pid=subp.pid
    print(f"cmd:{cmd} pid is {pid}")
    #ignore pid influence for now
    # pids="ps -e -o pgid,pid | awk -v p="+str(pid)+" '$1 == p {print $2}'"
    # subpids = subprocess.run(pids,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True,text=True)
    # outpids=subpids.stdout.strip().split('\n')
    # pids_num=len(outpids)
    # print(f"cmd has {pids_num} pids!")
    # print(f"cmd has pids: {outpids}")
    #pstree='pstree '+pid
    # try:
    #     subp.wait(3)
    #     if subp.poll() == 0:
    #         outs, errs=subp.communicate()
    #         #print(subp.communicate()[1])
    #     else:
    #         print("失败")
    try:
         outs, errs=subp.communicate(timeout=3)
    except subprocess.TimeoutExpired:
        #TODO kill process group 
        #os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        subp.kill()
        print(f'!timeout! cmd: {cmd}')
        outs, errs=subp.communicate()
        continue
    except UnicodeDecodeError:
        subp.kill()
        print(f"some encoding fault!")
        outs, errs=subp.communicate()
        continue
    print(f"cmd out:{outs}")
    print(f"cmd err:{errs}")
    findpid='dmesg | grep current:'+str(pid)
    subp = subprocess.run(findpid,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True,text=True)
    out=subp.stdout.strip().split('\n')
    err=subp.stderr.strip().split('\n')
    print(f"dmesg out:{out}")
    print(f"dmesg err:{err}")
    caps=[]
    caps_unique=set()
    res=""
    for o in out:
        if o=="":
            continue
        strcap=o.split(" ")[-1]
        caps.append(strcap)
        caps_unique.add(strcap)
    print(f"check cap seq: {caps}")
    for cap in caps_unique:
        cap_num=caps.count(cap)
        res=res+"check cap "+cap+" for "+str(cap_num)+" times,"
    if res:
        result={cmd:res}
        result_dict.update(result)
        print(result_dict)
#     print("out type is ")
#     print(type(outs))
#     print("errs type is ")
#     print(type(errs))
#     print(outs,errs)
#     if "not permitted" in errs or 'Permission denied' in errs:
#         findpid='dmesg | grep current:'+str(pid)
#         subp = subprocess.run(findpid,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True,text=True)
#         out=subp.stdout.strip().split('\n')
#         print(out)
#         caps=[]
#         caps_unique=set()
#         res=""
#         for o in out:
#             if o=="":
#                 continue
#             strcap=o.split(" ")[-1]
#             caps.append(strcap)
#             caps_unique.add(strcap)
#         print(f"check cap seq: {caps}")
#         for cap in caps_unique:
#             cap_num=caps.count(cap)
#             res=res+"check cap "+cap+" for "+str(cap_num)+" times,"
#         if res:
#             result={cmd:res}
#             result_dict.update(result)
# print(result_dict)
