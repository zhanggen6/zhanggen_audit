
import subprocess,random,string,datetime
from django.contrib.auth import authenticate
from django.conf import settings
from audit import models
from audit.backend import ssh_interactive

class UserShell(object):
    """用户登录堡垒机后的shell"""

    def __init__(self,sys_argv):
        self.sys_argv = sys_argv
        self.user = None

    def auth(self):

        count = 0
        while count < 3:
            username = input("username:").strip()
            password = input("password:").strip()
            user = authenticate(username=username,password=password)
            #None 代表认证不成功
            #user object ，认证对象 ,user.name
            if not user:
                count += 1
                print("Invalid username or password!")
            else:
                self.user = user
                return  True
        else:
            print("too many attempts.")

    def token_auth(self):
        count = 0
        while count < 3:
            user_input = input("请输入token:").strip()
            if len(user_input) == 0:
                return
            if len(user_input) != 8:
                print("token length is 8")
            else:
                time_obj = datetime.datetime.now() - datetime.timedelta(seconds=300)  # 5mins ago
                token_obj = models.Token.objects.filter(val=user_input, date__gt=time_obj).first()
                if token_obj:
                    if token_obj.val == user_input:  # 口令对上了
                        self.user = token_obj.account.user #进入交互式shll需要用户认证！
                        return token_obj
            count+=1
    def start(self):
        """启动交互程序"""
        token_obj = self.token_auth()
        if token_obj:
            ssh_interactive.ssh_session(token_obj.host_user_bind, self.user)
            exit()
        if self.auth():
            #print(self.user.account.host_user_binds.all()) #select_related()
            while True:
                host_groups = self.user.account.host_groups.all()
                for index,group in enumerate(host_groups):
                    print("%s.\t%s[%s]"%(index,group,group.host_user_binds.count()))
                print("%s.\t未分组机器[%s]"%(len(host_groups),self.user.account.host_user_binds.count()))
                try:
                    choice = input("select group>:").strip()
                    if choice.isdigit():
                        choice = int(choice)
                        host_bind_list = None
                        if choice >=0 and choice < len(host_groups):
                            selected_group = host_groups[choice]
                            host_bind_list = selected_group.host_user_binds.all()
                        elif choice == len(host_groups): #选择的未分组机器
                            #selected_group = self.user.account.host_user_binds.all()
                            host_bind_list = self.user.account.host_user_binds.all()
                        if host_bind_list:
                            while True:
                                for index,host in enumerate(host_bind_list):
                                    print("%s.\t%s"%(index,host,))
                                choice2 = input("select host>:").strip()
                                if choice2.isdigit():
                                    choice2 = int(choice2)
                                    if choice2 >=0 and choice2 < len(host_bind_list):
                                        selected_host = host_bind_list[choice2]

                                        ssh_interactive.ssh_session(selected_host,self.user)


                                        # s = string.ascii_lowercase +string.digits
                                        # random_tag = ''.join(random.sample(s,10))
                                        # session_obj = models.SessionLog.objects.create(account=self.user.account,host_user_bind=selected_host)
                                        #
                                        # cmd = "sshpass -p %s /usr/local/openssh/bin/ssh %s@%s -p %s -o StrictHostKeyChecking=no -Z %s" %(selected_host.host_user.password,selected_host.host_user.username,selected_host.host.ip_addr,selected_host.host.port ,random_tag)
                                        # #start strace ,and sleep 1 random_tag, session_obj.id
                                        # session_tracker_script = "/bin/sh %s %s %s " %(settings.SESSION_TRACKER_SCRIPT,random_tag,session_obj.id)
                                        #
                                        # session_tracker_obj =subprocess.Popen(session_tracker_script, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                                        #
                                        # ssh_channel = subprocess.run(cmd,shell=True)
                                        # print(session_tracker_obj.stdout.read(), session_tracker_obj.stderr.read())
                                        #
                                elif choice2 == 'b':
                                    break

                except KeyboardInterrupt as e :
                    pass

