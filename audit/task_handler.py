import json
import os
import subprocess

from django.conf import settings
from django.db.transaction import atomic

from audit import models

#Bestseller618

class Task(object):
    '''  '''

    def __init__(self, request):
        self.request = request
        self.errors = []
        self.task_data = None

    def is_valid(self):
        task_data = self.request.POST.get('task_data')  # {"task_type":"cmd","selected_host_ids":["1","2"],"cmd":"DF"}
        if task_data:
            self.task_data = json.loads(task_data)
            print(self.task_data)
            self.task_type = self.task_data.get('task_type')
            if self.task_type == 'cmd':
                selected_host_ids = self.task_data.get('selected_host_ids')
                if selected_host_ids:
                    return True
                self.errors.append({'invalid_argument': '命令/主机不存在'})

            elif self.task_type == 'file_transfer':  #
                selected_host_ids = self.task_data.get('selected_host_ids')
                self.task_type = self.task_data.get('task_type')

                if self.task_data.get('file_transfer_type'):  # get 下载
                    if self.task_data.get('remote_path'):
                        return True
                    self.errors.append({'invalid_argument': '远程路径不存在！'})

                # 验证上传文件路径
                user_id = models.Account.objects.filter(user=self.request.user).first().pk
                random_str = self.task_data.get('random_str')
                file_path = settings.FILE_UPLOADS + os.sep + str(user_id) + os.sep + random_str
                if os.path.isdir(file_path):
                    return True
                if not os.path.isdir(file_path):
                    self.errors.append({'invalid_argument': '上传路径失败，请重新上传'})
                if not selected_host_ids:
                    self.errors.append({'invalid_argument': '远程主机不存在'})



            else:
                self.errors.append({'invalid_argument': '不支持的任务类型！'})
        self.errors.append({'invalid_data': 'task_data不存在！'})

    def run(self):
        task_func = getattr(self, self.task_data.get('task_type'))  #
        task_obj = task_func()  # 调用执行命令
        # print(task_obj.pk)  # 100 #这里是任务id是自增的
        return task_obj

    @atomic  # 事物操作 任务信息和 子任务都要同时创建完成！
    def cmd(self):
        task_obj = models.Task.objects.create(
            task_type=0,
            account=self.request.user.account,
            content=self.task_data.get('cmd'),
        )  # 1.增加批量任务信息，并返回批量任务信息的 pk

        tasklog_objs = []  # 2.增加子任务信息（初始化数据库）
        host_ids = set(self.task_data.get("selected_host_ids"))  # 获取选中的主机id,并用集合去重
        for host_id in host_ids:
            tasklog_objs.append(models.TaskLog(task_id=task_obj.id,
                                               host_user_bind_id=host_id,
                                               status=3))
        models.TaskLog.objects.bulk_create(tasklog_objs, 100)  # 没100条记录 commit 1次!

        task_id = task_obj.pk
        cmd_str = "python %s %s" % (settings.MULTI_TASK_SCRIPT, task_id)  # 执行multitask.py脚本路径
        print('------------------>', cmd_str)
        multitask_obj = subprocess.Popen(cmd_str,shell=True, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)  # 新打开1个新进程

        # settings.CURRENT_PGID = os.getpgid(multitask_obj.pid)  # os.getpgid(multitask_obj.pid)
    
        # os.killpg(pgid=pgid,sig=signal.SIGKILL)

        # print(multitask_obj.stderr.read().decode('utf-8') or multitask_obj.stdout.read().decode('utf-8'))
        # print("task result :",multitask_obj.stdout.read().decode('utf-8'),multitask_obj.stderr.read().decode('utf-8'))
        # print(multitask_obj.stdout.read())

        # for host_id in self.task_data.get('selected_host_ids'):
        #     t=Thread(target=self.run_cmd,args=(host_id,self.task_data.get('cmd')))
        #     t.start()

        return task_obj

    @atomic  # 事物操作 任务信息和 子任务都要同时创建完成！
    def file_transfer(self):
        print(
            self.task_data)  # {'task_type': 'file_transfer', 'selected_host_ids': ['3'], 'file_transfer_type': 'send', 'random_str': 'iuon9bhm', 'remote_path': '/'}
        task_obj = models.Task.objects.create(
            task_type=1,
            account=self.request.user.account,
            content=json.dumps(self.task_data),
        )  # 1.增加批量任务信息，并返回批量任务信息的 pk

        tasklog_objs = []  # 2.增加子任务信息（初始化数据库）
        host_ids = set(self.task_data.get("selected_host_ids"))  # 获取选中的主机id,并用集合去重
        for host_id in host_ids:
            tasklog_objs.append(models.TaskLog(task_id=task_obj.id,
                                               host_user_bind_id=host_id,
                                               status=3))
        models.TaskLog.objects.bulk_create(tasklog_objs, 100)  # 没100条记录 commit 1次!

        task_id = task_obj.pk
        cmd_str = "python %s %s" % (settings.MULTI_TASK_SCRIPT, task_id)  # 执行multitask.py脚本路径
        print('------------------>', cmd_str)
        multitask_obj = subprocess.Popen(cmd_str, shell=True, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)  # 新打开1个新进程
        # settings.CURRENT_PGID = os.getpgid(multitask_obj.pid)  # os.getpgid(multitask_obj.pid)

        return task_obj
