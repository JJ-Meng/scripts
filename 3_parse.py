from operator import is_
from bs4 import BeautifulSoup
import re
import os
import json

titles=[]
args_dict={}
libres_dict={}

def handleshortopt(line):
    cmd=line.split(" ")[0]
    index=line.find("short opts:")
    opts=line[index+11:]
    opts=opts.replace("\n","")
    opt=""
    for char in opts:
        if char==":":
            index=opt.rfind(";")
            new_opt=opt[:index]+":"+opt[index:]
            opt=new_opt 
        elif char=="-":
            continue
        elif char=='?' or char=='h':
            continue
        else:
            opt=opt+"-"+char+";"
    #add to dict
    temp={cmd:opt}
    libres_dict.update(temp)
#libopt中的每选项是不是都在getoption找到的字典里，如果不在，说明manual过时,直接添加到optdict,还是否需要在manual中二次查找？
#manual中存在不在libopt的也能说明manual过时（暂不考虑？
def checkOptions(cmd,optdict,dup_opts):
    libopts=libres_dict.get(cmd).split(";")
    outdate=False
    print("liboptions optdict:")
    print(optdict)
    for lopt in libopts:
        #长选项预处理
        arg=""
        if lopt=="":
            continue
        if lopt.startswith("-")!=True and lopt!="":
            lopt="--"+lopt
            if lopt in dup_opts:
                continue
        #print("lib  opt is "+lopt)
        count=lopt.count(":")
        if count==1:
            arg="unknown"
        if count>0:
            lopt=lopt.replace(":","")
        if optdict.get(lopt)==None:
            outdate=True
            optdict.update({lopt:arg})
            #TODO 对于getopt误报处理，同一个选项，但是不同表达，去重
            #-i <device>,-d<device>,getopt.h会报告-d
            #定位-d，然后判断前面有没有‘，’？
            #print("++++++new opt from lib "+lopt)

    if outdate:
        #should remove
        print("++++++++++++++++++++++++manual outdate++++++++"+cmd)
        #f= open('res.txt','a+')
        #f.write("++++++++++++++++++++++++manual outdate++++++++"+cmd+'\n')
        #f.close()

def handlelongopt(line):
    cmd=line.split(" ")[0]
    index=line.find("long opts:")
    opts=line[index+10:]
    opts=opts.replace("\n","")
    old=libres_dict[cmd]
    new=""
    if old!="":
        new=old+opts
    else:
        new=opts
    temp={cmd:new}
    libres_dict.update(temp)

#处理libgetopt的结果,填充libres={"cmd":"短的选项以-开头"}
with open("2_libres100.txt","r",encoding="utf-8") as libres:
    content=libres.readlines()
    #print(content)
    for line in content:
        if "short opts:" in line:
            handleshortopt(line)
        elif "long opts:" in line:
            handlelongopt(line)
    #print("lib_dict:")
    #print(libres_dict)


def getSectionContent(h2):
    content=""
    new_content=""
    for next in h2.next_siblings:

        if next.name=="h2":
            break
        if next!=None:
            content=content+str(next)
    #TODO 被格式包围的br不能直接替换，需要保留格式标签,eg:<i><br>xxx</i>
    '''
    soup=BeautifulSoup(content,'html.parser')
    brs=soup.find_all("br")
    if brs:
        for br in brs:
            #if br!=None:
            print("find br")
            if br.previous_element.name=="b":
                #br.insert_after(soup.new_tag("b"))
                #br.append(soup.new_tag("b"))
            if br.previous_element.name=="i":
                br.insert_after(soup.new_string("<i>"))
                print("special br")
    content=str(soup)
    print(content)
    '''
    new_content=content.replace("\n"," ")
    if "<b><br/>" in content:
        new_content=new_content.replace("<b><br/>","</p><p><b>")
    elif "<i><br/>" in content:
        new_content=new_content.replace("<i><br/>","</p><p><i>")    
    elif "<br/>" in content:
        new_content=new_content.replace("<br/>","</p><p>")
    #html不认识<big>，将标签删除
    new_content=new_content.replace("<big>","")
    new_content=new_content.replace("</big>","")
    return new_content

#返回p的第一个非空子节点,单词，
def getFirstString(p):
    res=""
    for pchild in p.children:
        if pchild.string==None:
            continue
        b_string=pchild.string.strip().replace("\n"," ")
        b_string=b_string.split()[0]
        if b_string=="":
            continue
        else:
            res= b_string
            #print("get first "+b_string)
            break
    return res
#将一行是两个p
def getAbnormalSynopsis(temps,cmd):
    required=[]
    for temp in temps:
        cur=getNormalSynopsis(temp).strip()
        if cur!="":
            if not cur.startswith(cmd):     
                if required:
                    last=required[-1]
                    required.remove(last)
                    cur=last+" "+cur
                else:
                    print("err:cmd is "+cmd+" and current is "+cur)               
            required.append(cur)
    return required
#解析synposis入口
def getRequiredfromSyno(h2):
    new_content=getSectionContent(h2)
    local_soup=BeautifulSoup(new_content,'html.parser')
    temps=local_soup.find_all("p")
    required=[]
    #判断每个p是否初始字符串一样，都是命令
    cmd=""
    model=0
    for temp in temps:
        first=getFirstString(temp)
        #print(first)
        if cmd=="":
            cmd=first
        else:
            if cmd!=first:
                #print("cmd:"+cmd+" current first: "+first)
                model=1
                break
    if model==1:
        print("abnormal synopsis")
        required=getAbnormalSynopsis(temps,cmd)
    if model==0:
        print("normal synopsis")
        for t in temps:
            res=getNormalSynopsis(t).strip()
            if res not in required:
                required.append(res)
    #print(required)
    return required

#输入synopsis标签，输出必选参数列表
def getsimpleSynopsis(h2):
    '''
    content=getSectionContent(h2)
    local_soup=BeautifulSoup(content,'html.parser')
    temps=local_soup.find_all("p")
    required=[]
    '''
    require=""
    for sibling in h2.next_siblings:
        if sibling.string==None:
            continue
        if sibling.name=="h2":
            break
        if sibling.name=="p":
            p_str=sibling.string.strip().replace("\n","")
            #使用正则删除括号内的内容
            res=re.sub('\[[\[]*.*?[\]]*\]','',p_str)
            require=require+res+";"
            print("in getsimplesynopsis: "+require)
    return require
def delete_multi_brackets(old):
    state_stack = []
    new_s = ""
    for s in old:
        if s == '[':
            state_stack.append(s)
        elif s == ']':
            state_stack.pop()
        elif not state_stack:
            new_s += s
    return new_s

# 从synopsis中的每个<p>中提取必选部分,返回这个P中的必选部分，空格隔开元素，<i>标记是否为参数
def getNormalSynopsis(p):  
    prequired=""
    required_joint=""
    pstr=str(p).replace("\n"," ")
    #有的中括号里有</b> 
    # 删除括号内容   
    #res=re.sub('\[[\[]*.*?[\]]*\]','',pstr)
    res=pstr
    if '[' in pstr:
        res=delete_multi_brackets(pstr)
    res1=re.sub(r'\(.*\)','',res)
    b_count=res1.count("<b>")
    b_count1=res1.count("</b>")
    if b_count!=b_count1:
        res1=res1.replace("<b>","")
        res1=res1.replace("</b>","")  
    local_soup=BeautifulSoup(res1,'html.parser')
    temp=local_soup.find("p")
    for pchild in temp.children:
        if pchild.string==None:
            continue
        r_str=pchild.string.strip().replace("\n","")
        r_str=r_str.replace("...","")
        #黑名单过滤
        if "Usage:" in r_str:
            r_str=r_str.replace("Usage:","")
        #标记出参数名
        if pchild.name=="i":
            for s in r_str.split():
                required_joint=required_joint+" "+s+"<i>"
        else:
            required_joint=required_joint+" "+r_str
    if required_joint!="":
        prequired=prequired+required_joint+" "
    return prequired

#未启用
#synopsis中多行在一个<p>内 使用<br>换行
def getBrSynopsis(p):
    prequired=[]
    pstr=str(p).strip().replace("\n","")
    res=re.sub('\[[\[]*.*?[\]]*\]','',pstr)
    new_res=res.replace("<br/>","</p><p>")
    local_soup=BeautifulSoup(new_res,'html.parser')
    temps=local_soup.find_all("p")
    for temp in temps:
        line_require=getNormalSynopsis(temp).replace("...","")
        if line_require not in prequired:
            prequired.append(line_require)
    return prequired
#复杂命令报错，actions bridge，TODO
def handleOr(required):
    res=[]
    for req in required:
        if '|' in req:
            #remove kongge
            req=req.replace("| ","|")
            req=req.replace(" |","|")
            temps=req.split(" ")
         
            opts=[[],[],[],[],[]]
            #opts-[[]]*i
            tmp_res=[]
            cmd=""
            i=0
            for t in temps:
                if '|' in t:
                    opts[i]=t.split("|")                    
            m=0
            for t in temps:
                if t==" ":
                    continue
                if '|' in t:
                    if tmp_res:
                        for index in range(len(tmp_res)):
                            for o in opts[m]:
                                tmp_res[index]=tmp_res[index]+" "+o
                    else:
                        for o in opts[m]:
                            tmp_res.append(cmd+" "+o)
                    m=m+1
                else:
                    if tmp_res:
                        for index in range(len(tmp_res)):
                            tmp_res[index]=tmp_res[index]+" "+t
                    else:
                        cmd=cmd+" "+t
            res.extend(tmp_res)
        else:
            res.append(req)

    return res
#跳过tc系列命令，synopsis第一项是tc
def jump_tc(req):
    flag=False
    for r in req:
        if r.startswith("tc"):
            print("tc command unable to resolve!!")
            flag=True
            break
        elif r.startswith("btrfs"):
            print("btrfs command unable to resolve!!")
            flag=False
            break
    return flag

#提取区域里的加粗字符串(word) 作为命令的可能值
#TODO:每个命令都是一个单词么？区分command与option？
def getCommands(h,dict,arg_dict):
    content=getSectionContent(h)
    local_soup=BeautifulSoup(content,'html.parser')
    temps=local_soup.find_all("p")
    look_next=""
    for temp in temps:
        first=getFirstString(temp)
        for t in temp.children:
            if t.name=="b":
                b_str=t.string
                if first==b_str:
                    cmd_arg=""
                    for ie in t.next_siblings:
                        if ie.name=="i":
                            cmd_arg=ie.string
                    if cmd_arg:
                        b_str=b_str+"<"+cmd_arg+">"
                        look_next=cmd_arg
                    #添加到arg_dict<command:b_str>
                    old=dict.get("command")
                    new=""
                    if old!=None:
                        if old.find(b_str)==-1:
                            new=old+b_str+","
                        else:
                            new=old
                    else:
                        new=b_str+","
                    item='{"command":new}'
                    item_dd=eval(item)
                    dict.update(item_dd)
            elif look_next:
                getArgsinP(temp,look_next,arg_dict) 
    #print(dict)

def hasOptinSyno(h2):
    #print("hasOptinSyno")
    new_content=getSectionContent(h2)
    local_soup=BeautifulSoup(new_content,'html.parser')
    temps=local_soup.find_all("p")
    flag=False
    for temp in temps:
        p_str=str(temp).replace("\n","")
        raw=re.sub('\<.*?\>','',p_str)
        opts=re.findall(r'[\[](.*?)[\]]',raw)       
        for opt in opts:
            if opt.startswith('-'):
                flag=True
    return flag

def addto_dicts(res,options_dict):
    opt=res.split(":")[0]
    #选项以等号结尾
    if opt[-1]=="=":
        opt=opt.replace("=","")
    opt_arg=""
    look_next=""
    if res.endswith(":"):
        look_next=""
        #print("opt "+opt+" no arg")
    else:
        opt_arg=res.split(":")[1]
        look_next=opt_arg
    if options_dict.get(opt)==None:
        item='{opt:opt_arg}'
        item_dd=eval(item)
        #print(item_dd)
        options_dict.update(item_dd)
    return look_next
#def handlePforoptions(p):
#level:选项不是-开头的，目前会引入误报
def getOptins(h2,options_dict,arg_dict,dup_opts,level):
    new_content=getSectionContent(h2)
    local_soup=BeautifulSoup(new_content,'html.parser')
    temps=local_soup.find_all("p")
    look_next=""
    for temp in temps:
        res=extractfromP(temp,dup_opts,level)
        if res!="":
            #增加到字典
            look_next=addto_dicts(res,options_dict)
            #如果选项不是-开头，默认都去描述里找一下参数的合法值
            if level==1:
                look_next=res.split(":")[0]
            #if look_next:
                #print(look_next)
        else:
            if look_next:
                #print("look next for "+look_next)
                getArgsinP(temp,look_next,arg_dict) 
#从描述中提取特殊格式字符串作为参数的可能取值
def getArgsinP(p,arg_name,dict):
    for pchild in p.children:
        if pchild.string==None:
            continue
        string=pchild.string.replace("\n" ," ")
        #是否需要区分加粗和斜体
        '''
        if pchild.name=="b":
            if string:                
                print("bold arg value: "+pchild.string)
        if pchild.name=="i":
            if string:
                print("i arg value: "+pchild.string)
        '''
        #匹配特殊格式
        if pchild.name=="b" or pchild.name=="i":
            if string:
                #忽略可能是选项名的特殊格式字符串
                if string.startswith("-"):
                    continue
                old=dict.get(arg_name)
                if old!=None: 
                    if old.find(string)==-1:
                        string=old+string+","
                    else:
                        string=old
                else:
                    string=string+","
                if arg_name not in string:
                    item='{arg_name:string}'
                    item_arg=eval(item)
                    dict.update(item_arg)            
        #非特殊格式，匹配文件名和数字形式的字符串作为备选
        else:
            old=dict.get(arg_name)
            potential=""
            # 正则表达式提取文件
            expr=r'/[/\w\.]+'
            m=re.findall(expr,str(pchild.string))
            ms=set(m)
            if ms:
                for i in ms:
                    if old:
                        if i in old:
                            continue
                    potential=potential+i+","
            #正则提取数字
            #int_expr=r'[ ]\d+'
            #0~9
            int_expr=r'\b\d+\b'
            int_m=re.findall(int_expr,pchild.string)
            ints=set(int_m)
            if ints:
                for i in ints:
                    if old:
                        if i in old:
                            continue
                    potential=potential+i+","
            #正则匹配ip
            ip = re.findall(r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b", pchild.string)
            ips=set(ip)
            if ips:
                for i in ips:
                    if old:
                        if i in old:
                            continue
                    potential=potential+i+","

            if potential:
                new=""
                old=dict.get(arg_name)
                if old!=None: 
                    new=old+potential
                else:
                    new=potential
                if arg_name!=string:
                    item='{arg_name:new}'
                    item_arg=eval(item)
                    dict.update(item_arg) 
#提取example，是否用法都是加粗的           
def getExamples(h,cmd):
    examples=[]
    content=getSectionContent(h)
    local_soup=BeautifulSoup(content,'html.parser')
    temps=local_soup.find_all("p")
    for t in temps:
        for pchild in t.children:
            #example is bold
            if pchild.name=="b":
                b_string=pchild.string
                examples.append(b_string)
                #print(b_string)
    if not examples:
    #example is not bold,see if first word is cmd 
         for t in temps:
            fword=getFirstString(t)
            if fword==cmd:
                tmp=t.text
                print(tmp)
                examples.append(tmp)         
    return examples


#从<p>中提取选项和参数，前提是选项都加粗，参数都斜体,返回字符串“选项：参数名”
#-l loglevel j
def extractfromP(child,dup_opts,level):
    pre_parent=None
    opt_arg="" 
    res=""
    first=0
    '''
    if level==1:
        #不是-开头的选项，他应该有特殊格式
        s_origin=str(child['style'])
        if s_origin.find("margin-left")!=-1:
            index=s_origin.find("margin-left")+12
            index1=s_origin.find("%")
            ratio_s=s_origin[index:index1]
            ratio=int(ratio_s)
            if ratio>20:
                #print("desciption p")
                return res
    '''
    for pchild in child.children:
        #选项不一定被加粗。以-开头，p中的第一个元素足以判断是选项么
        #if pchild.name=="b":
        if pchild.text==None:
            continue
        b_string=pchild.text.strip().replace("\n"," ")
        if b_string=="":
            continue
        else:
            first=first+1
        #level==1如何区分选项和描述的P缩进大于20%?
        if b_string.startswith("-") or level==1:
            if pchild.parent is pre_parent:
                continue
            #为了筛选选项，假设选项是p的第一个元素 应该是除了换行之外的第一个元素
            #if pchild.previous_element.name!="p":
            if first!=1:
                continue
            if level==1 :
                if pchild.name!="b" and pchild.name !='i': 
                    continue
            #print(b_string)
            # 需要使用空格分隔么（-h -?）
            #空格分隔选项和参数名，‘，’或者‘|’分隔选项别名
            if b_string.find(" ")!=-1:
                opt_arg=b_string.split(" ")[1]
                if opt_arg.startswith("-"):
                    dup_opts.append(opt_arg)
                    opt_arg=""
                b_string=b_string.split(" ")[0]
            index=b_string.find(",")
            if index!=-1:
                b_string=b_string[0:index]
                dupopt=b_string[index:]
                if dupopt:
                    dup_opts.append(dupopt)
            else:
                index=b_string.find("|")
                if index!=-1:
                    b_string=b_string[0:index]
            #从尖括号中提取参数名
            if "<" in b_string:
                index1=b_string.find("<")
                opt_args=re.findall(r'[<](.*?)[>]',b_string)
                if len(opt_args)==1:
                    opt_arg=opt_args[0]
                b_string=b_string[0:index1]
            #print("extractfromP: "+b_string)
            pre_parent=next
            for ie in pchild.next_siblings:
                if ie.name=="i":
                    opt_arg=ie.string.replace("\n"," ")
                    if "<" in opt_arg:
                        opt_arg=opt_arg.replace("<","")
                        opt_arg=opt_arg.replace(">","")
                    break
            #-S spooldir
            if b_string.find(" ")!=-1:
                opt_arg=b_string.split(" ")[1]
                b_string=b_string.split(" ")[0]
            res=b_string+":"+opt_arg
    return res
duplicated=0
def resolve_cmd(html):
    with open(html,"r") as f:
        cur_cmd=html.split("/")[-1]
        cur_cmd=cur_cmd.split(".html")[0]
        #print("current command is "+cur_cmd)            
        print("*****resolve begin*****"+cur_cmd)
        options_dict={}
        #全局字典<arg:value>,value之间,分隔
        arg_dict={}
        dup_opts=[]
        content=f.read()
        required_all=[] 
        soup=BeautifulSoup(content,'html.parser')
        title=soup.find("title")
        if title.text not in titles:
            titles.append(title.string)
        else:
            print(title.text+" is duplicated")
            global duplicated
            duplicated=duplicated+1
            return

        name_content=""
        heads=soup.find_all("h2")
        opt_flag=False
        opt_sec=False
        options=None
        examples=[]
        for h in heads:
            # 从synopsis提取必选的参数或命令
            if "NAME" in h.text:
                #print("find NAME section")
                name_content=""
                for child in h.next_siblings:
                    if child.string!=None:
                        name_content=child.string.strip().split('-')[0]
                        if name_content:
                            print("cmd is "+name_content)
                            break
                        if child.name=="h2":
                            print("name section end")
                            if name_content=="":
                                print("Name not resolved")
                    
            if "SYNOPSIS" in h.text:
                #print("find synopsis section")
                required_all= getRequiredfromSyno(h)
                opt_flag=hasOptinSyno(h)
                if required_all:
                    '''
                    is_tc=jump_tc(required_all)
                    if is_tc:
                        break
                    '''
                    required_all= handleOr(required_all)
                    print("required part is ")
                    print(required_all)                     
            if "DESCRIPTION" in h.text:
                descript=h
                #getOptins(descript,options_dict,arg_dict)              
            if "COMMAND" in h.text:
                getCommands(h,options_dict,arg_dict)
            # 从options里提取选项和参数，基于选项参数都在p标签里且有特殊格式
            if "OPTIONS" in h.text:
                opt_sec=True
                options=h
                #print("find options section")
                getOptins(h,options_dict,arg_dict,dup_opts,0)
                #if dup_opts:
                #    print("dup opts:")
                #    print(dup_opts)
                #optimize with res from getopt.h
                if libres_dict.get(cur_cmd)!=None:
                    checkOptions(cur_cmd,options_dict,dup_opts)
                    #print("-----------------"+cur_cmd)
            if "EXAMPLE" in h.text:
                print("get example section")
                examples=getExamples(h,cur_cmd)
                if examples:
                    print("Examples:")
                    print(examples)
        if not bool(options_dict):
            print("no options resolved from OPTIONS")
            #print("has opt section:"+str(opt_sec))
            #print("has opt in synposis:"+str(opt_flag))
            if opt_sec:
                print("didnt resolve option section,consider options startswithout -")
                getOptins(options,options_dict,arg_dict,dup_opts,1)
            if opt_flag:
                print("has opt, try resolve from description")
                getOptins(descript,options_dict,arg_dict,dup_opts,0)
                if not bool(options_dict):
                    print("didn't find options in description")
        print("option dict:")
        print(options_dict)
        
        f = open('res.txt','a+')
        f.write("*********resolving "+cur_cmd+"******\n")
        json.dump(required_all,f)
        f.write("\n")
        json.dump(options_dict,f)
        f.write("\n")
        json.dump(arg_dict,f)
        f.write("\n")
        json.dump(examples,f)
        f.write("\n")
        if arg_dict:
            print("arg dict")
            print(arg_dict)
            for arg in arg_dict:
                item={arg:arg_dict[arg]}
                args_dict.update(item)     
        f.close()
        print("*****resolve end****")
#root_dir='E:\print_htmls'

#root_dir="C:\\Users\\MJZ\\OneDrive\\Documents\\研三\\capability\\command analyze\\html解析\\afterinstall_html"
# root_dir=u"C:\\Users\MJZ\\OneDrive\Documents\研三\capability\command analyze\html解析\print_htmls"
root_dir='/home/share/syz/scripts/afterinstall_html'
list = os.listdir(root_dir)
unresolved=0
for i in range(0,len(list)):
    path = os.path.join(root_dir,list[i])
    if os.path.isfile(path):
        size = os.path.getsize(path)
        if size==0:
            cmd=list[i].split(".")[0]
            #print(cmd+" has no manual")
            unresolved=unresolved+1
        else:
            resolve_cmd(path)

print("man is null can not resolve:"+str(unresolved))
print("try to resolve: "+str(len(titles)))
print("duplicated is "+str(duplicated))
#resolve_cmd("C:\\Users\\MJZ\\OneDrive\\Documents\\研三\\capability\\command analyze\\html解析\\afterinstall_html\\arp.html")
print("args_dict:")
print(args_dict)
f = open('res.txt','a+')
f.write("********* resolving end ******\n")
json.dump(args_dict,f)
f.write("\n")
f.close()
#resolve_cmd(u"C:\\Users\\MJZ\\OneDrive\\Documents\\研三\\capability\\command analyze\\html解析\\print_htmls\\arptables-save.html".encode("utf_8"))
# resolve_cmd("E:\\print_htmls\\arpd.html")
