from django.shortcuts import render,redirect,HttpResponse
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import signal

import json,os
from audit import models
import random,string
import datetime
from audit import task_handler
from django import conf
import zipfile
from wsgiref.util import FileWrapper #from django.core.servers.basehttp import FileWrapper

@login_required
def index(request):
    return render(request,'index.html')



def acc_login(request):
    error = ''
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username,password=password)
        if user:
            login(request, user)
            return  redirect(request.GET.get('next') or  '/')
        else:
            error = "Wrong username or password!"
    return render(request,'login.html',{'error':error })


@login_required
def acc_logout(request):
    logout(request)

    return  redirect('/login/')

@login_required
def host_list(request):

    return render(request,'hostlist.html')


@login_required
def get_host_list(request):
    gid = request.GET.get('gid')
    if gid:
        if gid == '-1':#未分组
            host_list = request.user.account.host_user_binds.all()
        else:
            group_obj = request.user.account.host_groups.get(id=gid)
            host_list = group_obj.host_user_binds.all()

        data = json.dumps(list(host_list.values('id','host__hostname','host__ip_addr','host__idc__name','host__port',
                                'host_user__username')))
        return HttpResponse(data)

@login_required
def get_token(request):
    bind_host_id=request.POST.get('bind_host_id')
    time_obj = datetime.datetime.now() - datetime.timedelta(seconds=300)  # 5mins ago
    exist_token_objs = models.Token.objects.filter(account_id=request.user.account.id,
                                                   host_user_bind_id=bind_host_id,
                                                   date__gt=time_obj)
    if exist_token_objs:  # has token already
        token_data = {'token': exist_token_objs[0].val}
    else:
        token_val=''.join(random.sample(string.ascii_lowercase+string.digits,8))

        token_obj=models.Token.objects.create(
            host_user_bind_id=bind_host_id,
            account=request.user.account,
            val=token_val)
        token_data={"token":token_val}

    return HttpResponse(json.dumps(token_data))



@login_required
def multi_cmd(request):
    """多命令执行页面"""
    return render(request,'multi_cmd.html')


@login_required
def multitask(request):
    task_obj = task_handler.Task(request)
    respose=HttpResponse(json.dumps(task_obj.errors))
    if task_obj.is_valid():      # 如果验证成功
        task_obj = task_obj.run()  #run()去选择要执行的任务类型，然后通过 getattr()去执行
        respose=HttpResponse(json.dumps({'task_id':task_obj.id,'timeout':task_obj.timeout,'task_type':task_obj.task_type})) #返回数据库pk task_id

    return respose


@login_required
def multitask_result(request):
    """多任务结果"""
    task_id = request.GET.get('task_id')

    task_obj = models.Task.objects.get(id=task_id)

    results = list(task_obj.tasklog_set.values('id','status',
                                'host_user_bind__host__hostname',
                                'host_user_bind__host__ip_addr',
                                'result'
                                ))

    return HttpResponse(json.dumps(results))





@login_required  #接收dropzone  上传的文件！
def multi_file_transfer(request):
    random_str = ''.join(random.sample(string.ascii_lowercase + string.digits, 8))
    #return render(request,'multi_file_transfer.html',{'random_str':random_str})
    return render(request,'multi_file_transfer.html',locals())

@login_required
@csrf_exempt
def task_file_upload(request):
    random_str = request.GET.get('random_str')
    upload_to = "%s/%s/%s" %(conf.settings.FILE_UPLOADS,request.user.account.id,random_str)
    if not os.path.isdir(upload_to):#如果用户文件 不存在 自动创建 exist_ok=True
        os.makedirs(upload_to,exist_ok=True)

    file_obj = request.FILES.get('file')
    f = open("%s/%s"%(upload_to,file_obj.name),'wb')
    for chunk in file_obj.chunks():
        f.write(chunk)
    f.close()
    print(file_obj)


    return HttpResponse(json.dumps({'status':0}))




def send_zipfile(request,task_id,file_path):

    zip_file_name = 'task_id_%s_files' % task_id
    archive = zipfile.ZipFile(zip_file_name , 'w', zipfile.ZIP_DEFLATED) #创建1个zip 包

    file_list = os.listdir(file_path) #找到堡垒机目录下 所有文件

    for filename in file_list:      #把所有文件写入 zip包中！
        archive.write('%s/%s' %(file_path,filename),arcname=filename)
    archive.close()
    #-------------------------------------------------------------- #文件打包完毕！

    wrapper = FileWrapper(open(zip_file_name,'rb')) #在内存中打开 打包好的压缩包

    response = HttpResponse(wrapper, content_type='application/zip') #修改Django的response的content_type
    response['Content-Disposition'] = 'attachment; filename=%s.zip' % zip_file_name #告诉流量器以 附件形式下载
    response['Content-Length'] = os.path.getsize(zip_file_name)               #文件大小
    #temp.seek(0)
    return response

@login_required
def task_file_download(request): #下载文件到本地
    task_id = request.GET.get('task_id')
    print(task_id)
    task_file_path = "%s/%s"%( conf.settings.FILE_DOWNLOADS,task_id)
    download_files=os.listdir(task_file_path)
    print(download_files)
    return send_zipfile(request,task_id,task_file_path) #调用打包函数


def end_cmd(request):
    current_task_pgid=settings.CURRENT_PGID
    os.killpg(current_task_pgid,signal.SIGKILL)
    return HttpResponse(current_task_pgid)

import json
import requests
class Get_biying(object):
    def get_one_photo(self):
        import json
        import requests
        url = r'http://cn.bing.com/HPImageArchive.aspx?format=js&idx=0&n=8'#&n=8设置获取图片的张数
        headers = {
            'User-Agent': 'Mozilla / 4.0(compatible;MSIE6.0;Windows NT 5.1)'
        }
        response = requests.get(url=url, headers=headers)

        dict_json = json.loads(response.text)
        list_photo = dict_json['images']
        dict_three = list_photo[4] #选择第几张图片
        url_photo = dict_three['url']
        url_photo = r'http://cn.bing.com' + url_photo
        return url_photo

def bi_ying(request):
    models.HostUserBind.objects.all()
    return render(request, 'test.html')