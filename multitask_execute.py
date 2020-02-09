import time,json
import sys,os
import multiprocessing
import paramiko
from django.conf import settings

def cmd_run(tasklog_id,task_obj_id,cmd_str,):

    import django
    django.setup()
    from audit import models
    tasklog_obj = models.TaskLog.objects.get(id=tasklog_id)
    print(tasklog_obj, cmd_str)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(tasklog_obj.host_user_bind.host.ip_addr,
                    tasklog_obj.host_user_bind.host.port,
                    tasklog_obj.host_user_bind.host_user.username,
                    tasklog_obj.host_user_bind.host_user.password,
                    timeout=15) #配置超时时间15秒！
    except Exception:
        tasklog_obj.result ='连接超时！'  # 如果没有 返回结果 /出现错误
        tasklog_obj.status = 2
        tasklog_obj.save()
        ssh.close()
    try:
        stdin, stdout, stderr = ssh.exec_command(cmd_str)
        result = stdout.read() + stderr.read() #执行错误信息或者 执行成功后输出
        ssh.close() #关闭ssh连接

        #修改子任务数据库结果
        tasklog_obj.result = result or '该命令没有输出结果！'#如果没有 返回结果 /出现错误
        tasklog_obj.status = 0
        tasklog_obj.save()

    except Exception as e:
        print("error :", e)
        tasklog_obj.result = str(e)  # 执行命令失败，错误信息 写入子任务日志
        tasklog_obj.status = 1
        tasklog_obj.save()
        ssh.close()

def file_transfer(tasklog_id,task_id,task_content):
    import django
    django.setup()
    from django.conf import settings
    from audit import models
    tasklog_obj = models.TaskLog.objects.get(id=tasklog_id)
    try:
        print('task contnt:', tasklog_obj)
        task_data = json.loads(tasklog_obj.task.content)

        t = paramiko.Transport((tasklog_obj.host_user_bind.host.ip_addr, tasklog_obj.host_user_bind.host.port))
        t.connect(username=tasklog_obj.host_user_bind.host_user.username, password=tasklog_obj.host_user_bind.host_user.password,)
        sftp = paramiko.SFTPClient.from_transport(t)

        if task_data.get('file_transfer_type') =='send':
            local_path = "%s/%s/%s" %( settings.FILE_UPLOADS,
                                       tasklog_obj.task.account.id,
                                       task_data.get('random_str'))
            print("local path",local_path)
            for file_name in os.listdir(local_path):
                sftp.put('%s/%s' %(local_path,file_name), '%s/%s'%(task_data.get('remote_path'), file_name))
            tasklog_obj.result = "send all files done..."

        else:
            # 循环到所有的机器上的指定目录下载文件

            download_dir = "{download_base_dir}/{task_id}".format(download_base_dir=settings.FILE_DOWNLOADS,
                                                                  task_id=task_id)
            if not os.path.exists(download_dir):#判断该批量任务的 下载目录是否存在！
                os.makedirs(download_dir,exist_ok=True)

            remote_filename = os.path.basename(task_data.get('remote_path')) #获取远程路径/tmp/test.py的文件名test.py用于拼接堡垒机下载路径
            local_path = "%s/%s.%s" %(download_dir,tasklog_obj.host_user_bind.host.ip_addr,remote_filename) #/文件下载路径/批量任务id/ipaddr.filename 堡垒机下载路径拼接完成！

            sftp.get(task_data.get('remote_path'),local_path ) #paramiko下载 必须输入 本地和远程的 绝对路径！

            tasklog_obj.result = 'get remote file [%s] to local done' %(task_data.get('remote_path')) #执行完毕给  子任务写入日志
        t.close()

        tasklog_obj.status = 0
        tasklog_obj.save()
        # ssh = paramiko.SSHClient()
        # ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    except Exception as e:
        print("error :",e )
        tasklog_obj.result = str(e) #执行错误 给  子任务写入错误日志
        tasklog_obj.save()




if __name__ == '__main__':
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.append(BASE_DIR)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zhanggen_audit.settings")
    import django
    django.setup()

    from audit import models
    task_id = sys.argv[1]
    from audit import models
    task_id=int(sys.argv[1])
    # 1. 根据Taskid拿到任务对象，
    # 2. 拿到任务关联的所有主机
    # 3.  根据任务类型调用多进程 执行不同的方法
    # 4 . 每个子任务执行完毕后，自己把 子任务执行结果 写入数据库 TaskLog表
    task_obj = models.Task.objects.get(id=task_id)

    pool=multiprocessing.Pool(processes=10) #开启 1个拥有10个进程的进程池

    if task_obj.task_type == 0:
        task_func=cmd_run
    else:
        task_func =file_transfer

    for task_log in task_obj.tasklog_set.all(): #查询子任务信息，并更新子任务，进入执行阶段！
        pool.apply_async(task_func,args=(task_log.id,task_obj.id,task_obj.content)) #开启子进程,把子任务信息的pk、和 批量任务的命令传进去！

    pool.close()
    pool.join()



