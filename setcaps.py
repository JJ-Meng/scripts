
import subprocess
import sys
import json
# input file: command and cap check(cmds_caps.txt)
#sys.argv[1]=/home/test/results/cmds_caps_1.txt
# outputfile: current command and capability(command name:cap_int[])
#sys.argv[2]=/home/test/results/cmds_capids_1.txt
def getlinkedfile(path):
    realpath=""
    filecmd='realpath '+path
    subp1=subprocess.run(filecmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,shell=True)
    realpath=subp1.stdout.strip()
    return realpath
#dict{cmd:[cap1,cap2]},script is a list for script type file, and elf is a list for elf file
#action controls it is a setcap or rmcap
def setcaps(cmd_caps_dict,script,elf,action):
    for key in cmd_caps_dict.keys():
        #whichcmds = ['which',key]
        whichcmd='which '+key
        subp = subprocess.run(whichcmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,shell=True)
        out=subp.stdout.strip()
        if out:
            filecmd='file '+out
            subp1=subprocess.run(filecmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,shell=True)
            fileout=subp1.stdout.strip()
            ELF_flag=False
            fp=""#cmd real path
            #normal execute file
            if 'ELF' in fileout:
                # print(out+' is ELF')
                ELF_flag=True
                fp=out
            #scripts file
            elif "ASCII" in fileout or 'text' in fileout:
                # print(out+' is script cannot use capability!')
                # print(fileout)
                script.append(out)
            #link file
            elif 'link' in fileout:
                # print(out+' is link')
                # print(fileout)
                linked=getlinkedfile(out)
                if linked:
                    # print(out+" realpath is "+linked)
                    #see if realpath is ELF
                    filecmd2='file '+linked
                    subp2=subprocess.run(filecmd2,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,shell=True)
                    fileout2=subp2.stdout.strip()
                    if "ELF" in fileout2:
                        ELF_flag=True
                        fp=linked
                        # print(" is ELF")
                else:
                    print("did not find realpath of "+out)
            if ELF_flag:
                if action==1:
                    val=cmd_caps_dict[key]
                    cap_val=""
                    for v in val:
                        #print(v)
                        cap_val=cap_val+str(v)+','
                    lastindex=cap_val.rfind(',')
                    cap_val=cap_val[0:lastindex]
                    setcap_cmd='setcap '+cap_val+"+eip "+fp
                    elf.append(fp)
                    print(setcap_cmd)
                    subp3=subprocess.run(setcap_cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,shell=True)
                    setcap_err=subp3.stderr.strip()
                    if setcap_err:
                        print("set cap err:"+setcap_err)
                        return False
                elif action==0:
                    setcap_cmd='setcap -r '+fp
                    print(setcap_cmd)
                    subp4=subprocess.run(setcap_cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,shell=True)
                    setcap_err=subp4.stderr.strip()
                    if setcap_err:
                        print("set cap err:"+setcap_err)
                        return False
    return True


with open(sys.argv[1],'r') as f:
    content=f.readlines()
    i=0
    cmd_caps_dict={}
    script=[]
    elf=[]
    for line in content:
        i=i+1
        # if i>4:
        #     continue
        if ':check cap' in line:
            caps=[]
            cmd_origin=""
            tmps=line.split('check cap ')
            j=0
            for t in tmps:
                j=j+1
                if j==1:
                    cmd_origin=t.split(' ')[0].replace(':',"")
                    
                    if '/' in cmd_origin:
                        lastname=cmd_origin.split('/')[-1]
                        if lastname in cmd_caps_dict.keys():
                            cmd_origin=lastname
                    continue
                cap=t.split(' ')[0]
                cap_int=int(cap)
                caps.append(cap_int)
            if cmd_caps_dict.get(cmd_origin)==None:
                item={cmd_origin:caps}
                cmd_caps_dict.update(item)
            else:
                values=cmd_caps_dict.get(cmd_origin)
                for c in caps:
                    if c in values:
                        continue
                    else:
                        values.append(c)
            #print(f'{cmd_origin} {caps}')
    print(cmd_caps_dict)
    f=open(sys.argv[2],'a+')
    json.dump(cmd_caps_dict,f)
    f.close()
    # setcaps(cmd_caps_dict,script,elf,0)
   
    
    script_count=len(script)
    print(f'find {script_count} script, script can not use capability to run')