with open('cmdscandidate.txt','r')as f:
	cmds=f.readlines()
	priv_cmd=set()
	targetcmd=set()
	for cmd in cmds:
		cmd = cmd.strip()
		if '/' in cmd:
			jump=False
			for t in targetcmd:
				if t in cmd:
					jump=True
					print(f'{cmd} is same as t,dont add to set')
			if jump:
				continue
		if cmd=="":
			continue
		cmd_origin=cmd.split(" ")[0]
		print(cmd_origin)
		targetcmd.add(cmd_origin)
	print(targetcmd)