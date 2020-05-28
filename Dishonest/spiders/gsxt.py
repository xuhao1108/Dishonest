# -*- coding: utf-8 -*-
import scrapy
import json
import time
import re
from lxml import etree
from jsonpath import jsonpath
from Dishonest.items import DishonestItem
from Dishonest.settings import FORMAT_TIME


class GsxtSpider(scrapy.Spider):
    name = 'gsxt'
    allowed_domains = ['gsxt.gov.cn']
    start_urls = ['http://www.gsxt.gov.cn/corp-query-entprise-info-xxgg-100000.html']
    url = 'http://www.gsxt.gov.cn/affiche-query-area-info-paperall.html?noticeType=11&areaid=100000&noticeTitle=&regOrg={}'

    def parse(self, response):
        # 获取响应的html文本
        html = etree.HTML(response.text)
        # 获取地区列表
        area_list = html.xpath("//div[@class='label-list']/div")
        for area in area_list:
            # 获取地区码和地区名称
            area_id = area.xpath('./@id')[0] if area.xpath('./@id') else ''
            area_name = area.xpath('.//text()')[0] if area.xpath('.//text()') else ''
            # 共5页，每页10条数据
            for page in range(0, 50, 10):
                # post参数
                params = {
                    # 每页起始值
                    'start': str(page),
                    'length': '10'
                }
                if area_id:
                    yield scrapy.FormRequest(url=self.url.format(area_id), formdata=params, callback=self.parse_data,
                                             meta={'area': area_name})

    def parse_data(self, response):
        # 获取数据并转换为json格式
        result = json.loads(response.text)
        # 获取失信企业数据
        datas = jsonpath(result, '$..data')[0] if jsonpath(result, '$..data') else ''
        # 依次取出每个失信企业信息
        for data in datas:
            # 获取失信企业名称
            name = re.findall('关?于?将?(.+)的?((列入)|(标记)|(清理)|(关于))', data['noticeTitle'])
            # 获取个体经营户法人代表
            business_entity = re.findall('经营者(.+)\)', data['noticeTitle'])
            # 获取失信企业注册号    （统一社会信用代码/注册号：(.+)）
            card_num = re.findall('注册号：(.+)）', data['noticeContent'])
            # 创建item对象，存放失信企业信息
            item = DishonestItem()
            item['name'] = name[0][0] if name else ''
            item['card_num'] = card_num[0] if card_num else ''
            item['age'] = 0
            item['area'] = response.meta['area']
            item['business_entity'] = business_entity[0] if business_entity else ''
            item['content'] = data['noticeContent']
            # 此时间单位为ms
            item['publish_date'] = time.strftime(FORMAT_TIME, time.localtime(int(data['noticeDate']) / 1000))
            item['publish_unit'] = data['judAuth_CN']
            item['create_date'] = time.strftime(FORMAT_TIME, time.localtime())
            item['update_date'] = time.strftime(FORMAT_TIME, time.localtime())
            yield item
