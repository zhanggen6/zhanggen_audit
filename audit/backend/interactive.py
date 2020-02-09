import socket
import sys
from paramiko.py3compat import u
from audit import models

# windows does not have termios...
try:
    import termios
    import tty

    has_termios = True
except ImportError:
    has_termios = False


def interactive_shell(chan, session_obj):
    if has_termios:  #
        posix_shell(chan, session_obj)  # unix 通用协议标准
    else:
        windows_shell(chan)


def posix_shell(chan, session_obj):
    import select

    oldtty = termios.tcgetattr(sys.stdin)
    try:
        tty.setraw(sys.stdin.fileno())
        tty.setcbreak(sys.stdin.fileno())
        chan.settimeout(0.0)
        flag = False
        cmd = ''
        while True:  # 开始输入命令
            r, w, e = select.select([chan, sys.stdin], [], [])  # 循环检测 输入、输出、错误，有反应就返回，没有就一直夯住！

            if chan in r:  # 远程 由返回 命令结果
                try:
                    x = u(chan.recv(1024))
                    if len(x) == 0:
                        sys.stdout.write('\r\n*** EOF\r\n')
                        break
                    if flag:  # 如果用户输入的Tab补全，服务器端返回
                        cmd += x
                        flag = False
                    sys.stdout.write(x)
                    sys.stdout.flush()
                except socket.timeout:
                    pass

            if sys.stdin in r:  # 本地输入
                x = sys.stdin.read(1)  # 输入1个字符就发送远程服务器
                if len(x) == 0:
                    break
                if x == '\r':  # 回车·
                    models.AuditLog.objects.create(session=session_obj, cmd=cmd)
                    cmd = ''
                elif x == '\t':  # tab 本地1个字符+远程返回的
                    flag = True
                else:
                    cmd += x
                chan.send(x)  # 发送本地输入 到远程服务器

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldtty)


# thanks to Mike Looijmans for this code
def windows_shell(chan):
    import threading

    sys.stdout.write("Line-buffered terminal emulation. Press F6 or ^Z to send EOF.\r\n\r\n")

    def writeall(sock):
        while True:
            data = sock.recv(256)
            if not data:
                sys.stdout.write('\r\n*** EOF ***\r\n\r\n')
                sys.stdout.flush()
                break
            sys.stdout.write(data)
            sys.stdout.flush()

    writer = threading.Thread(target=writeall, args=(chan,))
    writer.start()

    try:
        while True:
            d = sys.stdin.read(1)
            if not d:
                break
            chan.send(d)
    except EOFError:
        # user hit ^Z or F6
        pass