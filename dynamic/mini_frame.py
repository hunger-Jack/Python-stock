import time
import re
import logging
import urllib.parse
from pymysql import *

# 定义全局变量来映射url和函数的关系,使用装饰器自动添加映射关系
URL_FUNC_DICT = dict()

def route(url):
    def set_func(func):
        URL_FUNC_DICT[url] = func  # func是函数的指引
        # print("---------------->%s, %s<-------------------" % (str(url), str(func)))
        def call_func(*args, **kwargs):
            return func()
        return call_func
    return set_func


@route(r"/index.html")
def index(ret):
    """首页"""
    with open("./templates/index.html", "r") as f:
        content = f.read()

    # 1. 创建Connection连接
    conn = connect(host="localhost", port=3306, user="root", password="123qwe", database="stock_db", charset="utf8")
    
    # 2. 获得游标对象
    cs = conn.cursor()

    # 3. 执行sql
    cs.execute("select * from info;")
    stock_infos = cs.fetchall()

    # 4. 关闭游标和Connection
    cs.close()
    conn.close()

    # 替换模板数据
    html = ""
    tr_template = """<tr>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>
            <input type="button" value="添加" id="toAdd" name="toAdd" systemIdVaule="%s">
        </td>
        </tr>"""
    for info_line in stock_infos:
        html += tr_template % (info_line[0], info_line[1], info_line[2], info_line[3], info_line[4], info_line[5], info_line[6], info_line[7], info_line[1])
    content = re.sub(r"\{%content%\}", html, content)

    return content


@route(r"/center.html")
def center(ret):
    """个人中心"""
    with open("./templates/center.html", "r") as f:
        content = f.read()
     # 1. 创建Connection连接
    conn = connect(host="localhost", port=3306, user="root", password="123qwe", database="stock_db", charset="utf8")
    
    # 2. 获得游标对象
    cs = conn.cursor()

    # 3. 执行sql
    cs.execute("select i.code,i.short,i.chg,i.turnover,i.price,i.highs,f.note_info from info as i inner join focus as f on f.info_id=i.id;")
    stock_infos = cs.fetchall()

    # 4. 关闭游标和Connection
    cs.close()
    conn.close()

    # 替换模板数据
    html = ""
    tr_template = """
        <tr>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>
                <a type="button" class="btn btn-default btn-xs" href="/update/%s.html"> <span class="glyphicon glyphicon-star" aria-hidden="true"></span> 修改 </a>
            </td>
            <td>
                <input type="button" value="删除" id="toDel" name="toDel" systemIdVaule="%s">
            </td>
        </tr>
    """
    for info_line in stock_infos:
        html += tr_template % (info_line[0], info_line[1], info_line[2], info_line[3], info_line[4], info_line[5], info_line[6], info_line[0], info_line[0])
    content = re.sub(r"\{%content%\}", html, content)

    return content


# 给路由添加正则表达式的原因：在实际开发时，url中往往会带有很多参数，例如/add/000007.html中000007就是参数，
# 如果没有正则的话，那么就需要编写N次@route来进行添加 url对应的函数 到字典中，此时字典中的键值对有N个，浪费空间
# 而采用了正则的话，那么只要编写1次@route就可以完成多个 url例如/add/00007.html /add/000036.html等对应同一个函数，此时字典中的键值对个数会少很多
@route(r"/add/(\d+)\.html")
def add_focus(ret):
    """关注"""
    
    # 0. 获取股票代码
    stock_code = ret.group(1)

    # 1. 判断股票代码是否存在
    conn = connect(host="localhost", port=3306, user="root", password="123qwe", database="stock_db", charset="utf8")
    cs = conn.cursor()
    sql = "select * from info where code=%s;"
    cs.execute(sql, stock_code)
    # 如果不存在此股票代码就关闭游标和Connection，如果存在就进行下一步查询
    if not cs.fetchone():
        cs.close()
        conn.close()
        return "没有查询到此股票代码。。。%s" % stock_code

    # 2. 判断是否关注过此代码
    sql = "select f.info_id from info as i inner join focus as f on f.info_id=i.id where code=%s;"
    cs.execute(sql, stock_code)
    # 如果关注过代码就关闭游标和Connection，如果存在就进行下一步查询
    if cs.fetchone():
        cs.close()
        conn.close()
        return "已经关注过此股票，无须再次关注"

    # 3. 添加关注
    sql = "insert into focus(info_id) select id from info where code = %s;"
    cs.execute(sql, stock_code)
    conn.commit()
    cs.close()
    conn.close()

    return "关注 (%s) 成功...." % stock_code


@route(r"/del/(\d+)\.html")
def del_focus(ret):
    """取消关注"""
    
    # 0. 获取股票代码
    stock_code = ret.group(1)

    # 1. 判断股票代码是否存在
    conn = connect(host="localhost", port=3306, user="root", password="123qwe", database="stock_db", charset="utf8")
    cs = conn.cursor()
    sql = "select * from info where code=%s;"
    cs.execute(sql, stock_code)
    # 如果不存在此股票代码就关闭游标和Connection，如果存在就进行下一步查询
    if not cs.fetchone():
        cs.close()
        conn.close()
        return "没有查询到此股票代码。。。%s" % stock_code

    # 2. 判断是否关注过此代码
    sql = "select f.info_id from info as i inner join focus as f on f.info_id=i.id where code=%s;"
    cs.execute(sql, stock_code)
    # 如果没有关注过代码就关闭游标和Connection，如果关注过就进行下一步查询
    if not cs.fetchone():
        cs.close()
        conn.close()
        return "还没有关注过此股票，无法删除"

    # 3. 取消关注
    sql = "delete from focus where info_id = (select id from info where code = %s);"
    cs.execute(sql, stock_code)
    conn.commit()
    cs.close()
    conn.close()

    return "取消关注  (%s) 成功...." % stock_code


@route(r"/update/(\d+)\.html")
def show_update_page(ret):
    """打开修改备注信息页面"""

    # 1. 获取修改信息静态资源
    stock_code = ret.group(1)
    with open("./templates/update.html", "r") as f:
        content = f.read()

    # 2. 获取对应股票代码的备注信息
    conn = connect(host="localhost", port=3306, user="root", password="123qwe", database="stock_db", charset="utf8")
    cs = conn.cursor()
    sql = """select f.note_info from info as i inner join focus as f on f.info_id=i.id where code=%s;"""
    cs.execute(sql, (stock_code,))
    stock_comment = cs.fetchone()[0]
    cs.close()
    conn.close()

    # 把信息插入到对应模板
    content = re.sub(r"\{%code%\}", stock_code, content)
    content = re.sub(r"\{%note_info%\}", stock_comment, content)

    return content


@route(r"/update/(\d+)/(.*)\.html")
def save_update_page(ret):
    """保存修改备注信息"""

    # 1. 获取股票代码和要修改的备注信息
    stock_code = ret.group(1)
    stock_comment = ret.group(2)
    stock_comment = urllib.parse.unquote(stock_comment)  # 浏览器会对url编码，需要先解码在存入数据库

    # 2. 把修改的信息插入数据库
    conn = connect(host="localhost", port=3306, user="root", password="123qwe", database="stock_db", charset="utf8")
    cs = conn.cursor()
    sql = """update focus set note_info=%s where info_id = (select id from info where code=%s);"""
    cs.execute(sql, (stock_comment, stock_code))
    conn.commit()
    cs.close()
    conn.close()

    # 3. 返回修改成功的状态
    return "此：%s 股票备注信息修改成功" % stock_code



def application(env, start_response):
    """框架入口"""

    logging.basicConfig(level=logging.INFO,  
                    filename='./log.txt',  
                    filemode='a',  
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
    
    start_response("200 OK", [("Content-Type", "text/html; charset=UTF-8")])
    file_name = env["PATH_INFO"]

    logging.info("访问 %s" % file_name)

    try:
        for url, func in URL_FUNC_DICT.items():
            ret = re.match(url, file_name)
            # print("===============>%s, %s<===============" % (str(url), str(func)))
            if ret:
                return func(ret)
        else:
            return "没有找对 %s 对应的函数" % file_name
    except Exception as ret:
        return "产生了异常-%s" % str(ret)