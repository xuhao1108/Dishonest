# -*- coding: utf-8 -*-
import scrapy
import json
from jsonpath import jsonpath
import time
from Dishonest.items import DishonestItem
from Dishonest.settings import FORMAT_TIME


class CourtSpider(scrapy.Spider):
    name = 'court'
    allowed_domains = ['court.gov.cn']
    url = 'http://jszx.court.gov.cn/api/front/getPublishInfoPageList'

    # post请求需重写start_requests方法
    def start_requests(self):
        # post参数
        params = {
            'pageSize': '10',
            'pageNo': '1',
        }
        yield scrapy.FormRequest(url=self.url, formdata=params, callback=self.parse)

    def parse(self, response):
        # 获取数据并转换为json格式
        result = json.loads(response.text)
        # 获取数据总数
        page_count = jsonpath(result, '$.pageCount')[0] if jsonpath(result, '$.pageCount') else ''
        # 获取每页数据
        for page in range(page_count):
            # post参数
            params = {
                'pageSize': '10',
                'pageNo': str(page),
            }
            yield scrapy.FormRequest(url=self.url, formdata=params, callback=self.parse_data)

    def parse_data(self, resonse):
        # 获取数据并转换为json格式
        result = json.loads(resonse.text)
        # 获取失信人数据
        datas = jsonpath(result, '$.data')[0] if jsonpath(result, '$.data') else ''
        # 依次取出每个失信人信息
        for data in datas:
            # 创建item对象，存放失信人信息
            item = DishonestItem()
            item['name'] = data['name']
            item['card_num'] = data['cardNum']
            item['age'] = data['age']
            item['area'] = data['areaName']
            item['business_entity'] = data['buesinessEntity']
            item['content'] = data['duty']
            item['publish_date'] = time.strftime(FORMAT_TIME, time.localtime(int(data['publishDate'])))
            item['publish_unit'] = data['gistUnit']
            item['create_date'] = time.strftime(FORMAT_TIME, time.localtime())
            item['update_date'] = time.strftime(FORMAT_TIME, time.localtime())
            yield item
