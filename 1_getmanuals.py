import os
import subprocess
import re
#command='man -Thtml blktrace > blktrace.html'
command='blktrace'
def addcmd(command):
	res='man -Thtml '+command+' > blktrace.html'
	return res

def cmd(command):
    subp = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    out=subp.stdout.readlines()
    err=subp.stderr.readlines()
    return err,out

def installcmd(command):
	err=cmd(command)
	howtoinstall="wget https://command-not-found.com/"+command+" -O 1.html"
	print(howtoinstall)
	errs,outs=cmd(howtoinstall)
	print(errs)
	grep='grep "apt-get install" 1.html'
	err,out=cmd(grep)
	print(out)
	out_str=""
	for i in out:
		out_str=out_str+i.decode("utf-8")
	print(out_str)
	installcmd=""
	for o in out_str.splitlines():
		if "<" in out_str:
			installcmd=re.sub('\<.*?\>','',o)
		if installcmd:
			break
	if installcmd:
		installcmd="sudo "+installcmd
	else:
		print("err in get install command")
		return 
	print("installcmd:"+installcmd)
	err,out=cmd(installcmd)
	print("err:")
	print(err)
	print("out:")
	print(out)
	'''
	installcmd=re.sub('\<.*?\>','',grep)
	print(installcmd)
	cmd(installcmd)
	'''

	  
if __name__ == '__main__':
	cur_cmd=addcmd(command)
	err=cmd(cur_cmd)
	for e in err:
		if "No manual entry" in str(e):
				print("command need to be install")
				installcmd(command)	
	

