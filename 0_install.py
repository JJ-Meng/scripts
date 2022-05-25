import subprocess
import os
import re
def installcmd(command):
	res=False
	howtoinstall="wget https://command-not-found.com/"+command+" -O 1.html"
	print(howtoinstall)
	subhow = subprocess.run(howtoinstall,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	grep='grep "apt-get install" 1.html'
	subgrep = subprocess.run(grep,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
	out=subgrep.stdout.strip()
	err=subgrep.stderr.split('\n')

	installcmd=""
	for o in out.splitlines():
		if "<" in o:
			installcmd=re.sub('\<.*?\>','',o)
		if installcmd:
			break
	if installcmd:
		installcmd = installcmd + " -y"
	else:
		print("err in get install command")
		return
	#print("installcmd:"+installcmd)
	install_res=os.system(installcmd)
	if install_res==0:
		res=True
		print(command+"install successed")
	else:
		print(command+"install err is "+str(install_res))
	return res 
	

if __name__ == '__main__':
	hascmd=0
	install=0
	failtoinstall=[]
	with open("cmdlist","r") as f:
		c=0
		for line in f.readlines():
			if "(8)" in line:
				idx=line.index("(8)")
				command=line[0:idx]
				cmd_all="which "+command
				c=c+1
				if c<100:
					#print(command)
					s=""#command path
					subp = subprocess.run(cmd_all,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
					s=subp.stdout.strip()
					#err=subp.stderr.readlines()
					if s:
						hascmd=hascmd+1						
					else:
						install=install+1
						res=installcmd(command)
						if res:
							install=install+1
						else:
							failtoinstall.append(command)
	print(f"{hascmd} is already on VM")
	print(f"{install} is installed")
	print(f"failed to install {failtoinstall}")