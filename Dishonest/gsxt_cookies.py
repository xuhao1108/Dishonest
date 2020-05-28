from gevent import monkey

monkey.patch_all()

import re
import js2py
import requests
import random
import pickle
from redis import StrictRedis
from gevent.pool import Pool
from Dishonest.settings import REDIS_URL, COOKIES_REDIS_KEY
from Dishonest.settings import USER_AGENTS_LIST
from Dishonest.settings import COOKIES_HEADERS_UA, COOKIES_PROXY, COOKIES_COOKIES


class GsxtCookies(object):
    def __init__(self):
        # 连接redis
        self.redis = StrictRedis.from_url(REDIS_URL)
        # 创建携程池对象
        self.pool = Pool()

    def gen_cookies(self):
        while True:
            try:
                # 获取session对象
                session = requests.session()
                # 获取执行js的对象
                js = js2py.EvalJs()
                # 随机获取一个请求头
                user_agent = random.choice(USER_AGENTS_LIST)
                # 获取代理ip
                proxy = requests.get('http://127.0.0.1:8888/random?protocol=http').text
                # 设置session请求头
                session.headers['User-Agent'] = user_agent
                # 设置session代理
                session.proxies = {
                    'http': proxy
                }

                url = 'http://www.gsxt.gov.cn/corp-query-entprise-info-xxgg-100000.html'
                # 发送第一次请求
                response = session.get(url=url)
                # 获取script代码
                script = re.findall('<script>(.+?)</script>', response.text)[0]
                # 将eval函数转换为code变量
                script = script.replace('eval(', 'code=(')
                # 执行script代码
                js.execute(script)

                # 获取code代码段
                code_result = js.code
                # 获取code代码段中的cookie变量
                cookie = re.findall("document\.(cookie='.+)};", code_result)[0]
                # 执行cookie代码段
                js.execute(cookie)
                # 获取code代码段的执行结果：key=value形式
                cookie_result = re.findall('(__jsl_clearance)=(.+?);', js.cookie)[0]
                # 将js执行结果中的cookies添加到session的cookies中
                session.cookies.set(cookie_result[0], cookie_result[1])

                # 再次发送请求
                session.get(url=url)
                # 获取字典格式的session中的cookies
                cookies = requests.utils.dict_from_cookiejar(session.cookies)
                if '__jsl_clearance' in cookies and '__jsluid_h' in cookies and 'SECTOKEN' in cookies:
                    # 保存关联的headers，proxy，cookies信息
                    gsxt_cookies = {
                        COOKIES_HEADERS_UA: user_agent,
                        COOKIES_PROXY: proxy,
                        COOKIES_COOKIES: cookies,
                    }
                    # 将信息存入redis中
                    self.redis.lpush(COOKIES_REDIS_KEY, pickle.dumps(gsxt_cookies))
                    print(gsxt_cookies)
                    break
            except Exception as e:
                pass
                # print(e)

    def run(self):
        # 清空之前存放的信息
        self.redis.delete(COOKIES_REDIS_KEY)
        for i in range(100):
            # 创建异步执行任务
            self.pool.apply_async(self.gen_cookies)
        # 让主线程等待所有携程任务完成
        self.pool.join()

    def __del__(self):
        # 关闭redis连接
        self.redis.close()


if __name__ == '__main__':
    x = GsxtCookies()
    x.run()
