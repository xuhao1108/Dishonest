# -*- coding: utf-8 -*-
import scrapy
import json
import time
from jsonpath import jsonpath
from Dishonest.items import DishonestItem
from Dishonest.settings import FORMAT_TIME


class BaiduSpider(scrapy.Spider):
    name = 'baidu'
    allowed_domains = ['baidu.com']
    start_urls = [
        'https://sp0.baidu.com/8aQDcjqpAAV3otqbppnN2DJv/api.php?resource_id=6899&query=失信被执行人&pn=0&rn=10&from_mid=1']

    def parse(self, response):
        # 获取数据并转换为json格式
        result = json.loads(response.text)
        # 获取数据总数
        disp_num = jsonpath(result, '$..dispNum')[0] if jsonpath(result, '$..dispNum') else 0
        # 基础url格式
        base_url = 'https://sp0.baidu.com/8aQDcjqpAAV3otqbppnN2DJv/api.php?' \
                   'resource_id=6899&query=失信被执行人&pn={}&rn=10&from_mid=1'
        # 获取每页数据，第一页的pn=0，第二页pn=10
        for page in range(0, disp_num, 10):
            # 补全url
            url = base_url.format(page)
            yield scrapy.Request(url=url, callback=self.parse_data)

    def parse_data(self, response):
        # 获取数据并转换为json格式
        result = json.loads(response.text)
        # 获取失信人数据
        datas = jsonpath(result, '$..disp_data')[0] if jsonpath(result, '$..disp_data') else ''
        # 依次取出每个失信人信息
        for data in datas:
            # 创建item对象，存放失信人信息
            item = DishonestItem()
            item['name'] = data['iname']
            item['card_num'] = data['cardNum']
            item['age'] = data['age']
            item['area'] = data['areaName']
            item['business_entity'] = data['businessEntity']
            item['content'] = data['duty']
            item['publish_date'] = time.strftime(FORMAT_TIME, time.localtime(int(data['publishDateStamp'])))
            item['publish_unit'] = data['gistUnit']
            item['create_date'] = time.strftime(FORMAT_TIME, time.localtime())
            item['update_date'] = time.strftime(FORMAT_TIME, time.localtime())
            yield item
