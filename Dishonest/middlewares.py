# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

# from scrapy import signals


# class DishonestSpiderMiddleware(object):
#     # Not all methods need to be defined. If a method is not defined,
#     # scrapy acts as if the spider middleware does not modify the
#     # passed objects.
#
#     @classmethod
#     def from_crawler(cls, crawler):
#         # This method is used by Scrapy to create your spiders.
#         s = cls()
#         crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
#         return s
#
#     def process_spider_input(self, response, spider):
#         # Called for each response that goes through the spider
#         # middleware and into the spider.
#
#         # Should return None or raise an exception.
#         return None
#
#     def process_spider_output(self, response, result, spider):
#         # Called with the results returned from the Spider, after
#         # it has processed the response.
#
#         # Must return an iterable of Request, dict or Item objects.
#         for i in result:
#             yield i
#
#     def process_spider_exception(self, response, exception, spider):
#         # Called when a spider or process_spider_input() method
#         # (from other spider middleware) raises an exception.
#
#         # Should return either None or an iterable of Request, dict
#         # or Item objects.
#         pass
#
#     def process_start_requests(self, start_requests, spider):
#         # Called with the start requests of the spider, and works
#         # similarly to the process_spider_output() method, except
#         # that it doesn’t have a response associated.
#
#         # Must return only requests (not items).
#         for r in start_requests:
#             yield r
#
#     def spider_opened(self, spider):
#         spider.logger.info('Spider opened: %s' % spider.name)
#
#
# class DishonestDownloaderMiddleware(object):
#     # Not all methods need to be defined. If a method is not defined,
#     # scrapy acts as if the downloader middleware does not modify the
#     # passed objects.
#
#     @classmethod
#     def from_crawler(cls, crawler):
#         # This method is used by Scrapy to create your spiders.
#         s = cls()
#         crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
#         return s
#
#     def process_request(self, request, spider):
#         # Called for each request that goes through the downloader
#         # middleware.
#
#         # Must either:
#         # - return None: continue processing this request
#         # - or return a Response object
#         # - or return a Request object
#         # - or raise IgnoreRequest: process_exception() methods of
#         #   installed downloader middleware will be called
#         return None
#
#     def process_response(self, request, response, spider):
#         # Called with the response returned from the downloader.
#
#         # Must either;
#         # - return a Response object
#         # - return a Request object
#         # - or raise IgnoreRequest
#         return response
#
#     def process_exception(self, request, exception, spider):
#         # Called when a download handler or a process_request()
#         # (from other downloader middleware) raises an exception.
#
#         # Must either:
#         # - return None: continue processing this exception
#         # - return a Response object: stops process_exception() chain
#         # - return a Request object: stops process_exception() chain
#         pass
#
#     def spider_opened(self, spider):
#         spider.logger.info('Spider opened: %s' % spider.name)
import re
import requests
import random
import pickle
from redis import StrictRedis
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from Dishonest.spiders.gsxt import GsxtSpider
from Dishonest.settings import REDIS_URL, COOKIES_REDIS_KEY, COOKIES_HEADERS_UA, COOKIES_PROXY, COOKIES_COOKIES
from Dishonest.settings import PROXY_URL, USER_AGENTS_LIST


class DishonestHeadersMiddleware(object):
    def process_request(self, request, spider):
        if not isinstance(spider, GsxtSpider):
            # 随机获取一个请求头
            request.headers['User-Agent'] = random.choice(USER_AGENTS_LIST)
        return None


class DishonestProxyMiddleware(object):
    def process_request(self, request, spider):
        if not isinstance(spider, GsxtSpider):
            # 随机获取一个代理ip
            proxy = self.get_random_proxy(request.url)
            if proxy:
                # 设置代理ip
                request.meta['proxy'] = proxy
        return None

    def process_response(self, request, response, spider):
        if response.status != 200 or response.body == b'':
            # 随机获取一个代理ip
            proxy = self.get_random_proxy(request.url)
            if proxy:
                # 设置代理ip
                request.meta['proxy'] = proxy
            return request
        return response

    def process_exception(self, request, exception, spider):
        # 判断当前异常
        if isinstance(exception, RetryMiddleware.EXCEPTIONS_TO_RETRY):
            # 获取异常的代理ip的url
            proxy = request.meta['proxy']
            # 获取代理ip位置
            # 截取代理ip
            ip = re.findall('://(.+):', proxy)[0] if re.findall('://(.+):', proxy) else ''
            # 设置此代理ip的不可用域名
            url = '{}/disable_domain'.format(PROXY_URL)
            # 获取此url的domain
            domain = re.findall('\.(.+\.(com|cn))', request.url)
            domain = domain[0] if domain else ''
            domain = domain[0] if domain else ''
            # 参数
            params = {
                'ip': str(ip),
                'domain': domain
            }
            # 更新此代理ip的不可用域名
            requests.get(url, params=params)
            return request

    def get_random_proxy(self, url):
        # 获取代理ip的url
        url = '{}/random'.format(PROXY_URL)
        # 获取url类型
        protocol = re.findall('(.+?)://', url)
        # 参数
        params = {
            'protocol': protocol[0] if protocol else ''
        }
        # 发送请求，获取代理ip
        response = requests.get(url=url, params=params)
        # 获取代理ip
        proxy = response.text
        # 判断是否获取到代理ip
        if proxy:
            # 获取代理ip协议类型
            proxy_protocol = re.findall('(.+?)://', proxy)
            # 若无协议类型，则添加默认协议类型http
            proxy = proxy if proxy_protocol else 'http://' + proxy
            return proxy
        else:
            return None


class DishonestGsxtCookiesMiddleware(object):
    def __init__(self):
        # 连接redis数据库
        self.redis = StrictRedis.from_url(REDIS_URL)

    def process_request(self, request, spider):
        if isinstance(spider, GsxtSpider):
            # 获取redis数据库中存放的数据长度
            cookies_len = self.redis.llen(COOKIES_REDIS_KEY)
            # 从redis数据库随机获取一条信息
            cookies_bytes = self.redis.lindex(COOKIES_REDIS_KEY, random.randrange(0, cookies_len))
            # 反序列化
            cookies_dict = pickle.loads(cookies_bytes)
            # 设置request请求头
            request.headers['User-Agent'] = cookies_dict[COOKIES_HEADERS_UA]
            # 设置request代理ip
            request.meta['proxy'] = cookies_dict[COOKIES_PROXY]
            # 设置request cookies
            request.cookies = cookies_dict[COOKIES_COOKIES]
            # 设置不要重定向
            request.meta['dont_redirect'] = True
        return None

    def process_response(self, request, response, spider):
        if response.status != 200 or response.body == b'':
            # 备份请求
            req = request.copy()
            # 设置请求不过滤
            # req.dont_fliter = True
            return req
        return response
