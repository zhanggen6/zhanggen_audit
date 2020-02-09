#!/usr/bin/python3
# -*- coding: utf-8 -*
import sys,os,django
os.environ.setdefault("DJANGO_SETTINGS_MODULE","zhanggen_audit.settings")
django.setup() #在Django视图之外，调用Django功能设置环境变量！
from audit.backend import user_interactive


if __name__ == '__main__':
    shell_obj=user_interactive.UserShell(sys.argv)
    try:
        shell_obj.start()
    except KeyboardInterrupt:
        print('the process end !')


