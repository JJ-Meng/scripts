import json
from signal import SIGKILL
import subprocess
import os
import sys
#need 2 files:
# (1)input file sys.argv[1]
# (2)output file sys.argv[2]
perm_targets=['Permission','permission','permitted','Permitted','root','Root','ROOT','superuser','Superuser','Privilege','privilege']
res=[] #potential privilege cmd and outputs
err="" #log err message


#先记录所有{cmd:pid}，再去dmesg找pid有问题，因为dmesg会被冲掉
#cmd_pid={} 

#def getcaps(pid,cmd,output):
def getcaps(pid,cmd,dict):
	'''
	privflag=False
	if len(output)>1000:
		return privflag
	

	temp_res=cmd+'\n'+"out: "+output
	global res
	res.append(temp_res)
	privflag=True
	'''
	findpid="dmesg | grep '#cap_capable# current:'"+str(pid)
	subp = subprocess.run(findpid,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True,text=True)
	out=subp.stdout.strip().split('\n')
	#print(out)
	caps=[]#检查的所有caps
	caps_unique=set()#检查了哪些cap
	cmdres=""
	if not out:
		return False
	for o in out:
		if o=="":
			continue
		strcap=o.split(" ")[-1]
		caps.append(strcap)
		caps_unique.add(strcap)
	for cap in caps_unique:
		cap_num=caps.count(cap)
		cmdres=cmdres+"check cap "+cap+" for "+str(cap_num)+" times,"
	if cmdres:
		result={cmd:cmdres}
		dict.update(result)
		# print(cmdres)
		return True
	return False
def getuids(pid):
	flag=0 #0 no check;1 uid check;2 gid check;3 for both
	finduchecks="dmesg | grep 'uid current:'"+str(pid)
	subp1 = subprocess.run(finduchecks,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True,text=True)
	if subp1.stdout.strip():
		flag=flag+1
	findgchecks="dmesg | grep 'gid current:'"+str(pid)
	subp2 = subprocess.run(findgchecks,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True,text=True)
	if subp2.stdout.strip():
		flag=flag+2
	return flag

#level0:uid0+all cap    level1:uid0+14cap   level3:uid0+no cap
#level4:uid normal+all  
# def runcmds(cmdspath,outfp,targets):
def runcmds(cmdspath,outfp,userset):
	#/home/test/results/cmds_caps_1.txt
	result_dict={}
	with open(cmdspath,'r')as f:
		cmds=f.readlines()
		priv_count=0
		line_num=0
		priv_cmd=set()
		targetcmd=set()
		last_cmd=""
		has_priv=0
		non_privcmd=set()
		# non_privcmd=""
		for cmd in cmds:
			cmd = cmd.strip()
			line_num=line_num+1
			# if line_num>10:
			# 	continue
			#print(cmd)	
			#fuzz end
			if "*****" in cmd:
				break	
			if cmd=="":
				continue
			#dont fuzz agetty
			if 'agetty' in cmd:
				continue
			jump=False
			cmd_origin=""
			#使用绝对路径的cmd
			if '/' in cmd:
				for t in targetcmd:
					if t in cmd:
						jump=True
						cmd_origin=t
					if t==cmd:
						jump=False
						cmd_origin=t
						#print(f'{cmd} is same as t,dont add to set')
			if jump==False:			
				cmd_origin=cmd.split(" ")[0]
				targetcmd.add(cmd_origin)
			#	print(f"{cmd} origin is {cmd_origin}")
			if last_cmd!=cmd_origin:
				if has_priv==0 and last_cmd!="":
					# non_privcmd=non_privcmd+last_cmd+"\n"
					non_privcmd.add(last_cmd)
				#new cmd
				last_cmd=cmd_origin
				has_priv=0
			# if cmd_origin not in targets:
			# 	targetcmd.discard(cmd_origin)
			# 	continue
			#cmd='sudo '+cmd
			#question:what if there are " in cmd?
			# cmd='su test -c "'+cmd+'"'	
			# print(cmd)
			#会保留多余空格
			#cmd_list=cmd.split(" ")
			cmd_list=cmd.split()

			try:
				#user=1000
				subp = subprocess.Popen(cmd_list,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
				pid=subp.pid
				temp={cmd:pid}
				#cmd_pid.update(temp)
				print(f"cmd:{cmd} pid is {pid}")
				outs, errs=subp.communicate(timeout=3)
			except subprocess.TimeoutExpired:
				# subp.kill()
				# os.kill(pid,SIGKILL)#
				os.system("sudo kill %s" % (pid))
				print(f'!timeout! cmd: {cmd}')
				outs, errs=subp.communicate()
				continue
			except UnicodeDecodeError:
				# subp.kill()
				print(f"some encoding fault!")
				continue
			except FileNotFoundError:
				# subp.kill()
				print(f"file not found! outs:{outs}  errs:{errs}")
				continue
			# check if there are keywords in output
			'''
			privflag=False		
			for t in perm_targets:
				if t in outs:
					privflag=getcaps(pid,cmd,outs)
					
				if t in errs:
					privflag=getcaps(pid,cmd,errs)
			if privflag:
				priv_count=priv_count+1
				priv_cmd.add(cmd_origin)
			'''
			if getcaps(pid,cmd,result_dict):
				priv_count=priv_count+1
				priv_cmd.add(cmd_origin)
				has_priv=has_priv+1
				# print(f"{cmd} is privilege")
			if getuids(pid)>0:
				userset.add(cmd)
			# else:
				# print(f"{cmd} is not privilege")
				#non_privcmd=non_privcmd+cmd+"\n"		
	
	priv_target_count=len(priv_cmd)
	totaltargets=len(targetcmd)
	npriv_target=totaltargets-priv_target_count
	#/home/test/results/cmds_caps_1.txt
	f = open(outfp,'a+',encoding="UTF8")
	#permission keywords
	# for r in res:
	# 	f.write(r)
	# 	cmd=r.split('\n')[0]
	# 	cmd=cmd.strip()
	# 	if result_dict.get(cmd)!=None:
	# 		f.write(f"{cmd}:{result_dict[cmd]}\n")
	# 		f.write('\n')
	for item in result_dict:
		f.write(f"{item}:{result_dict[item]}\n")
		f.write('\n')
	f.write("non-privilege commands are:\n")
	for non in non_privcmd:
		f.write(non)
		f.write('\n')
	f.write("*****************final results********************************\n")
	f.write(f"fuzz {line_num} commands in total,and {priv_count} commands are privilege\n")
	f.write(f"target cmds:{totaltargets}  priv target cmds:{priv_target_count} non-priv cmds:{npriv_target}\n")
	f.write("target commands are: ")
	for t in targetcmd:
		f.write(t)
		f.write('\n')
	f.close()
	print("**********cmd and caps*******")
	for r in result_dict:
		print(f"{r}:{result_dict[r]}")
	print("*****************final results********************************")
	#print(result_dict)
	print(f"fuzz {line_num} commands in total,and {priv_count} commands are privilege")
	print(f"target cmds:{totaltargets}  priv target cmds:{priv_target_count} non-priv cmds:{npriv_target}\n")
	#target-priv_cmd->non_priv_target
	non_priv=set()
	# for t in targets:
	# 	if t not in priv_cmd:
	# 		non_priv.add(t)
	# 		#print(f"non priv tar:{t}")
	# for np in non_priv:
	# 	targets.discard(np)
	#print(f"after run target is {targets}")
	 

def getlinkedfile(path):
    realpath=""
    filecmd='realpath '+path
    subp1=subprocess.run(filecmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,shell=True)
    realpath=subp1.stdout.strip()
    return realpath

def setcaps_new(dict,action):
	if action==1:
		for f in dict:
			setcap_cmd="setcap all+eip "+f
			subp=subprocess.run(setcap_cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,shell=True)
			setcap_err=subp.stderr.strip()
			if setcap_err:
				# err=err+"set cap err:"+setcap_err+'\n'
				print("set cap err:"+setcap_err)
	elif action==0:
		for f in dict:
			setcap_cmd="setcap -r "+f
			subp1=subprocess.run(setcap_cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,shell=True)
			setcap_err=subp1.stderr.strip()
			if setcap_err:
				# err=err+"set cap err:"+setcap_err+'\n'
				print("set cap err:"+setcap_err)
#dict{cmd:[cap1,cap2]},script is a list for script type file, and elf is a list for elf file
#action controls it is a setcap or rmcap
def setcaps(dict,action):
    # for key in cmd_caps_dict.keys():
    #     #whichcmds = ['which',key]
    #     whichcmd='which '+key
    #     subp = subprocess.run(whichcmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,shell=True)
    #     out=subp.stdout.strip()
    #     if out:
    #         filecmd='file '+out
    #         subp1=subprocess.run(filecmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,shell=True)
    #         fileout=subp1.stdout.strip()
    #         ELF_flag=False
    #         fp=""#cmd real path
    #         #normal execute file
    #         if 'ELF' in fileout:
    #             # print(out+' is ELF')
    #             ELF_flag=True
    #             fp=out
    #         #scripts file
    #         elif "ASCII" in fileout or 'text' in fileout:
    #             # print(out+' is script cannot use capability!')
    #             # print(fileout)
    #             script.append(out)
    #         #link file
    #         elif 'link' in fileout:
    #             # print(out+' is link')
    #             # print(fileout)
    #             linked=getlinkedfile(out)
    #             if linked:
    #                 # print(out+" realpath is "+linked)
    #                 #see if realpath is ELF
    #                 filecmd2='file '+linked
    #                 subp2=subprocess.run(filecmd2,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,shell=True)
    #                 fileout2=subp2.stdout.strip()
    #                 if "ELF" in fileout2:
    #                     ELF_flag=True
    #                     fp=linked
    #                     # print(" is ELF")
    #             else:
    #                 print("did not find realpath of "+out)
    #         if ELF_flag:
    #             if action==1:
    #                 val=cmd_caps_dict[key]
    #                 cap_val=""
    #                 for v in val:
    #                     #print(v)
    #                     cap_val=cap_val+str(v)+','
    #                 lastindex=cap_val.rfind(',')
    #                 cap_val=cap_val[0:lastindex]
    #                 setcap_cmd='setcap '+cap_val+"+eip "+fp
    #                 elf.append(fp)
    #                 print(setcap_cmd)
    #                 subp3=subprocess.run(setcap_cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,shell=True)
    #                 setcap_err=subp3.stderr.strip()
    #                 if setcap_err:
    #                     print("set cap err:"+setcap_err)
    #                     return False
    #             elif action==0:
    #                 setcap_cmd='setcap -r '+fp
    #                 print(setcap_cmd)
    #                 subp4=subprocess.run(setcap_cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,shell=True)
    #                 setcap_err=subp4.stderr.strip()
    #                 if setcap_err:
    #                     print("set cap err:"+setcap_err)
    #                     return False
	if action==1:
		for key in dict.keys():
			val=dict[key]
			cap_val=""
			for v in val:
				cap_val=cap_val+str(v)+','
			lastindex=cap_val.rfind(',')
			cap_val=cap_val[0:lastindex]
			setcap_cmd='setcap '+cap_val+"+eip "+key
			subp3=subprocess.run(setcap_cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,shell=True)
			setcap_err=subp3.stderr.strip()
			if setcap_err:
				err=err+"set cap err:"+setcap_err+'\n'
				print("set cap err:"+setcap_err)
			
	elif action==0:
		for key in dict.keys():
			setcap_cmd='setcap -r '+key
			#print(setcap_cmd)
			subp4=subprocess.run(setcap_cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,shell=True)
			setcap_err=subp4.stderr.strip()
			if setcap_err:
				err=err+"set cap err:"+setcap_err+'\n'
				print("set cap err:"+setcap_err)

#infp:input file. should  contain cmd:check cap xx m times
#outfp:output file. log after each run cmd:caps[int]
def runres(infp,outfp):
	with open(infp,'r') as f:
		content=f.readlines()
		i=0
		cmd_caps_dict={}
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
		print(f'cmd cap dict:{cmd_caps_dict}')
		f=open(outfp,'a+')
		json.dump(cmd_caps_dict,f)
		f.close() 
		print("***********cmd and caps int**********")
		print(cmd_caps_dict)
		return cmd_caps_dict

def getcmdfile(cmd):
	fp=""#cmd real path
	ELF_flag=False
	whichcmd="which "+cmd
	subp = subprocess.run(whichcmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,shell=True)
	out=subp.stdout.strip()
	if out:
		filecmd='file '+out
		subp1=subprocess.run(filecmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,shell=True)
		fileout=subp1.stdout.strip()
		
		#normal execute file
		if 'ELF' in fileout:
			ELF_flag=True
			fp=out
		#scripts file
		elif "ASCII" in fileout or 'text' in fileout:
			fp=out
		#link file
		elif 'link' in fileout:
			linked=getlinkedfile(out)
			if linked:
				# print(out+" realpath is "+linked)
				#see if realpath is ELF
				filecmd2='file '+linked
				subp2=subprocess.run(filecmd2,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,shell=True)
				fileout2=subp2.stdout.strip()
				if "ELF" in fileout2:
					fp=linked
					ELF_flag=True
			else:
				print("did not find realpath of "+out)
	return ELF_flag,fp

#get dict{filepath:caps}
def checkfiletype(capdict,scripts):
	filecapdict={}
	for key in capdict.keys():
		#whichcmds = ['which',key]
		elf,fp=getcmdfile(key)
		if elf:
			item={fp:capdict[key]}
			filecapdict.update(item)
		else:
			scripts.append(fp)
			# print(f"{fp} is probabaly a script,can not use capabality")
	return filecapdict 

def getallcmds(cmdfile):
	cmds=set()
	with open(cmdfile,'r') as f:
		content=f.readlines()
		for line in content:
			if "*****" in line:
				break
			if " " in line:
				cmd=line.strip().split()[0]
			else:
				cmd=line
			if '/' in cmd:
				cmd_origin=cmd.split('/')[-1]
				if cmd_origin in cmds:
					continue
				else:
					cmds.add(cmd)
			cmds.add(cmd)
	return cmds

def getfinalres(interfp,finalfp):
	with open(interfp,'r') as f:
		content=f.readlines()
	i=0
	cmd_caps_dict={}
	for line in content:
		i=i+1
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
	# print(cmd_caps_dict)
	for cmd in cmd_caps_dict:
		print(f"{cmd}:{cmd_caps_dict[cmd]}")
	f=open(finalfp,'a+')
	json.dump(cmd_caps_dict,f)
	f.close()

#sys.argv[1]:/home/test/results/run0/cap_cmds.txt
#sys.argv[2]: /home/test/results/run0/cmd_capid.txt
if __name__ == "__main__":
	cur_caps_dict={}
	last_caps_dict={}
	script=[]
	filecap_dict={}
	new_run=set()
	userset=set()
	# get unique command set from all fuzzing command
	# new_run=getallcmds('/home/test/scripts/ground-truth-1.txt')
	new_run=getallcmds('/home/test/scripts/badblocks.txt')

	for cmd in new_run:
		elf,file=getcmdfile(cmd)
		if elf:
			item={file:""}
			filecap_dict.update(item)
		else:
			script.append(file)
	#sub priority is normal uid+all cap
	#setcaps_new(filecap_dict,1)
	#run fuzz and log
	# runcmds('/home/test/scripts/ground-truth-1.txt','/home/test/results/truth-run/internal2-badb.txt')
	runcmds('/home/test/fuzz_cmd/cmds20.txt','/home/test/results/run2/cmds20new-i1.txt',userset)
	# runcmds()
	#get cmd:caps(id)
	getfinalres('/home/test/results/run2/cmds20new-i1.txt','/home/test/results/run2/cmds20new-f1.txt')
	#  getcap_cmd="getcap /usr/sbin/arpd"
	# subp=subprocess.run(getcap_cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,shell=True)
	# getcap=subp.stdout.strip()
	# print(getcap)
	#setcaps_new(filecap_dict,0)
	print("script cannot have capability")
	print(script)
	print("userspace check uid")
	print(userset)
	# for i in range(3):
	# 	new_filecap_dict={}
	# 	tmp_interf=sys.argv[1].split('.txt')[0]+'_'+str(i)+'.txt'
	# 	print(tmp_interf)
	# 	tmp_resf=sys.argv[2].split('.txt')[0]+'_'+str(i)+'.txt'
	# 	print(tmp_resf)
	# 	if i==0:
	# 		#get all cmds
	# 		new_run=getallcmds('/home/test/scripts/cmdscandidate.txt')
	# 		print(new_run)
	# 	if not new_run:
	# 		print(f' at run {i} target empty break')
	# 		break
	# 	else:
	# 		print(f'before run target:{new_run}')
	# 	#run fuzz cmd and log cmds and caps
	# 	runcmds('/home/test/scripts/cmdscandidate.txt',tmp_interf,new_run)
	# 	print(f'after run target:{new_run}')
	# 	#log cmd:cap and set cap for cmd file
	# 	cur_caps_dict=runres(tmp_interf,tmp_resf)
	# 	if last_caps_dict:
	# 		for key in cur_caps_dict:
	# 			last=set(last_caps_dict[key])
	# 			current=set(cur_caps_dict[key])
	# 			samevalue=last&current
	# 			if len(samevalue)==len(last)==len(current):
	# 				print(f'{key} analyze end')
	# 				new_run.discard(key)
	# 			else:
	# 				last_caps_dict[key]=cur_caps_dict[key]
	# 				elf,fp=getcmdfile(key)
	# 				item={fp:cur_caps_dict[key]}
	# 				filecap_dict.update(item)
	# 				print(f'{key} need a new run')
	# 	else:#first time run
	# 		last_caps_dict=cur_caps_dict
	# 		print(f'new run required')
	# 		#first time should check if file is script or elf
	# 		filecap_dict=checkfiletype(cur_caps_dict,script)
	# 		new_filecap_dict=filecap_dict			
	# 	setcaps(new_filecap_dict,1)
	# print(f"file cap dict:{filecap_dict}")
	# print(f"final cmds and cap:{last_caps_dict}")
	# script_count=len(script)
	# print(f'find {script_count} script, script can not use capability to run')
	# print(f'script is {script}')
	# # setcap -r
	# setcaps(filecap_dict,0)


