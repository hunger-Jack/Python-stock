import time
import sys
import socket
import re
import multiprocessing


class WSGIServer(object):
    """web server 对象"""
    def __init__(self, port, app, static_path):
        # 1. 创建套接字
        self.tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 防止服务器先挥手导致，fd被占用

        # 2. 绑定信息
        self.tcp_server_socket.bind(("", port))

        # 3. 变为监听套接字
        self.tcp_server_socket.listen(128)

        # 接受框架里面application函数
        self.application =  app

        # 接受静态文件路径
        self.static_path = static_path

    def service_client(self, new_socket):
        """为客户端返回消息"""

        # 接受消息
        request = new_socket.recv(1024).decode("utf-8")
        request_lines = request.splitlines()
        print("")
        print(">" * 50)
        print(request_lines)

        # 获取url路由,如果是“/”，设置为“index.html”
        # GET /index.html HTTP/1.1
        file_name = ""
        ret = re.match(r"[^/]+(/[^ ]*)", request_lines[0])
        if ret:
            file_name = ret.group(1)
            
            if file_name == "/":
                file_name = "/index.html"

        # 返回http格式的消息
        # 如果文件不是以.py结尾的请求，就是静态资源请求
        if not file_name.endswith(".html"):
            try:
                f = open(self.static_path + file_name, 'rb')
            except:
                response = "HTTP/1.1 404 NOT FOUND\r\n"
                response += "\r\n"
                response += "-----file not found-----"
            else:
                html_content = f.read()
                f.close()
                response = "HTTP/1.1 200 OK\r\n"
                response += "\r\n"
                new_socket.send(response.encode("utf-8"))
                new_socket.send(html_content)
        # 以.py结尾的文件，就认为是动态资源请求
        else:
            env = dict()
            env["PATH_INFO"] = file_name
            body = self.application(env, self.set_response_header)
            header = "HTTP/1.1 %s\r\n" % self.status
            for temp in self.headers:
                header += "%s:%s\r\n" % (temp[0], temp[1])
            header += "\r\n"
            response = header + body
            new_socket.send(response.encode("utf-8"))
        # 关闭客户端套接字
        new_socket.close()

    def set_response_header(self, status, headers):
        """接受header信息"""
        self.status = status
        self.headers = [("server", "mini_frame 1.1")]
        self.headers += headers

    def run_forever(self):
        """完成整体控制"""

        while True:
            # 4. 等待新客户端连接
            new_socket, client_addr = self.tcp_server_socket.accept()

            # 5. 为这个客户服务
            p = multiprocessing.Process(target=self.service_client, args=(new_socket,))
            p.start()

            # 关闭客户端套接字，由于多进程会复制代码，所以这里也需要关闭
            new_socket.close()

        # 关闭监听套接字
        self.tcp_server_socket.close()


def main():

    # # 判断运行命令参数
    # if len(sys.argv) == 3:
    #     try:
    #         port = int(sys.argv[1])
    #         frame_app_name = sys.argv[2]
    #     except Exception as ret:
    #         print("端口输入错误。。。。")
    #         return
    # else:
    #     print("请按照以下方式输入")
    #     print("python3 xxxx.py 7890  frame_name:application")
    #     return

    # ret = re.match(r"([^:]+):(.*)", frame_app_name)
    # if ret:
    #     frame_name = ret.group(1)
    #     app_name = ret.group(2)
    # else:
    #     print("请按照以下方式输入")
    #     print("python3 xxxx.py 7890  frame_name:application")
    #     return

    # 加载配置文件
    with open("./web_server.cnf") as f:
        config_info = eval(f.read())

    sys.path.append(config_info["dynamic_path"])  # 从配置文件获取dynamic包路径，并且把dynamic文件路径加到模块导入路径
    port = int(config_info["port"])  # 从配置文件获取端口
    frame = __import__(config_info["frame_name"])  # 从配置文件获取模块名称，并且使用__import__函数可以使用变量导入模块，返回 标记这个导入的模块
    app = getattr(frame, config_info["app_name"])  # 从配置文件获取框架函数，返回frame模块里面app_name函数的指引
    static_path = config_info["static_path"]  # 从配置文件获取静态资源路径

    wsgi_server = WSGIServer(port, app, static_path)
    wsgi_server.run_forever()


if __name__ == "__main__":
    main()