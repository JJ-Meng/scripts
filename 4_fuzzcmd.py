from ast import arguments
from inspect import getargs
import json

'''
targets=['accessdb']
'''
targets=['30-systemd-environment-d-generator',
'accton','addpart','agetty','anacron'
,'arp'
,'arpd'
,'arping'
,'arptables-nft-restore'
,'arptables-nft-save'
,'astraceroute'
,'audispd-zos-remote'
,'auditctl'
,'auditd'
,'augenrules'
,'aureport'
,'ausearch'
,'automount'
,'autrace'
,'avcstat'
,'badblocks'
]
black_list=['tc','bpfc','bridge','btrfs']
argus=[]
opt_argname=[]
first_res=[]
sec_res=[]
#dictionary:2 dict
syno_dict={'ipaddr':'hostname,destination','macaddr':'hw_addr','device':'device','interface':'ifname','integer':'start,length,partition,port','program':'program','file':'file,filename','directory':'directory'}
typeval_dict={'ipaddr':'127.0.0.1,192.168.119.138,182.61.200.7,10.0.2.10','macaddr':'00:0c:29:0d:19:d6','device':'/dev/sda, /dev/loop0p1','interface':'eth0',
'integer':'0,1,63,121212,65534','program':'/bin/ls','file':'/home/test/cmdfiles/normalfile.txt, /home/test/cmdfiles/arpdl.txt,/home/test/cmdfiles/auditrules,/home/test/cmdfiles/myarpdb.db,/home/test/cmdfiles/myissue',
'directory':'/home/test/cmdfiles'}
def getargs(line):
	args_dict=json.loads(line)
	for key in args_dict:
		if key not in opt_argname:
			opt_argname.append(key)

def assemble(req,opts,args,example):
	required=json.loads(req)
	opts_dict=json.loads(opts)
	args_dict=json.loads(args)
	example_dict=json.loads(example)
	res=[]
	tempres=""

#require + opt
	for r in required:
		#add required anyway
		if r not in res:
				res.append(r)
		#if [option] in require
		rwords=r.split()
		new_r=""
		# for rw in rwords:
		# 	id=rw.index(rwords)
		# 	if "option" in rw:
		# 		rwords[id]=""
		# 		continue
		# 	if '[' in rw or '<' in rw or ']' in rw or '>' in rw and (len(rw))==1:
		# 		rwords[id]=""
		# 		nextword=''
		# 	new_r=new_r+rwords[id]
		# r=new_r
		#synopsis has option already,dont iterate opts_dic
		if ' -' not in r and opts_dict:
			#res.append(r)
		#elif opts_dict:
			for i in opts_dict:
				arg=opts_dict[i]
				if arg!="":
					if args_dict.get(arg)!=None:
						tempargs=args_dict.get(arg).split(",")
						for a in tempargs:
							tempres=r+" "+i+" "+a
							res.append(tempres)
					#TODO:need argu but local argdict has no matching,try global dict
					else:
						for sy in syno_dict:
							if sy in arg.lower():
								tmpres=r+" "+i+" "+arg+'<i>'
								res.append(tmpres)
				else:
					tempres=r+" "+i
					res.append(tempres)
		
	for ex in example_dict:
		res.append(ex)
	if res:
		for tres in res:
			print(tres)
			id=res.index(tres)
			if '{' in tres:
				tres_list=tres.split()
				tresnew=""
				for tl in tres_list:
					if '{' in tl:
						tl=tl.replace('{',"")
						tl=tl.replace('}',"")
						tl=tl+'<i>'
					tresnew=tresnew+tl+" "
				tres=tresnew
				res[id]=tres
			#remove <> brefore <i>
			count=tres.count('<')
			if count>1:
				tres=tres.replace('<','',1)				
				tres=tres.replace('>','',1)
			elif '<i>' not in tres:
				tres=tres.replace('<','')
				tres=tres.replace('>',"")
			res[id]=tres			
			# if '<' in tres and '<i>' not in tres:
			# 	id=res.index(tres)
			# 	tres=tres.replace('<','')
			# 	tres=tres.replace('>',"")
			# 	res[id]=tres
			# extend argu dict
			

	# print("fuzzing cmds:")
	# print(res)
	first_res.extend(res)
	'''
	f = open('fuzz_cmds.txt','a+')
	json.dump(res,f)
	f.write('\n')
	f.close()
	'''

def handleres():	
	for r in first_res:
		tempres=""
		internal=[]
		if '<i>' in r:
			words=r.split()
			for word in words:
				if '<i>' in word:
					type=""
					arguname=word.replace("<i>","")
					# print(f'arguname is '+arguname)
					#big little case
					for key in syno_dict:
						if arguname.lower() in syno_dict[key]:
							type=key
							break
					if type:
						tval=typeval_dict[type]
						tvals=tval.split(',')
						ininternal=[]						
						if internal:
							for i in range(len(internal)):
								for val in tvals:
									ininternal.append(internal[i]+val+" ")
						internal=ininternal
					else:
						if type not in argus:
							argus.append(type)
						print("err:arguname not in synoyms dict!"+arguname)

				else:
					if internal:
						for i in range(len(internal)):
							internal[i]=internal[i]+word+" "
					else:
						tempres=tempres+word+" "
						internal.append(tempres)
			for temp_internal in internal:
				temp_internal=temp_internal.strip()
				if temp_internal not in sec_res:
					sec_res.append(temp_internal)
		else:
			r=r.strip()
			if r not in sec_res:
				sec_res.append(r)
	#print(f"final fuzz cmds {sec_res}")
with open('res.txt') as res:
	i=0
	required=''
	opts=''
	args=''
	example=''
	flag=False #only fuzz cmd in target
	while True:
		line=res.readline()
		if not line:
			break
		if i%5==0:
			cur_cmd=""		
			if "****"in line:
				cur_cmd=line.split(' ')[1].strip()
				cur_cmd=cur_cmd.replace("*","")
				if 'resolving' in cur_cmd:
					break
				print("cur_cmd is "+cur_cmd)
				if cur_cmd in targets:
				# if 'arpd' in cur_cmd:					
				#if cur_cmd not in black_list:
					print('assembling cmd '+cur_cmd)
					flag=True
				else:
					flag=False
		#get first word in require list,jump cmd if first in blklist 
		elif flag and i%5==1:
			required=line.strip()
			req=json.loads(required)
			if req:
				first=req[0].strip().split(' ')[0]
				print(f'first is '+first)
			#if first in black_list:
			# if first not in targets:
			# 	flag=False
			# 	print(flag)
			# else:
			# 	flag=True
			# 	print(flag)
			
		elif flag and i%5 ==2:
			opts=line.strip()
		elif flag and i%5==3:
			args=line.strip()
			getargs(line)
		elif flag and i%5==4:
			example=line
			assemble(required,opts,args,example)		
		i=i+1
	handleres()
	f = open('../fuzz_cmd/cmds20.txt','a+',encoding="UTF8")
	#f.write('final res -------------------\n')
	for final in sec_res:	
		f.write(final)
		f.write('\n')
	f.write('***********')
	f.write("arguments are:**************\n")
	for arg in argus:
		f.write(arg+"\n")
	f.write('\n\n')
	f.write("************opt args names are:***********\n")
	for a in opt_argname:
		f.write(a+'\n')
	f.write('\n')	
	#json.dump(sec_res,f)
	f.close()
	print("arguments are:")
	print(argus)
	print("opt args names are:")
	print(opt_argname)				