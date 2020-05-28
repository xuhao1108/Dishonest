# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class DishonestItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    # 失信人名称
    name = scrapy.Field()
    # 失信人证件号
    card_num = scrapy.Field()
    # 失信人年龄, 企业年龄都是0
    age = scrapy.Field()
    # 区域
    area = scrapy.Field()
    # 法人(企业)
    business_entity = scrapy.Field()
    # 失信内容
    content = scrapy.Field()
    # 公布日期
    publish_date = scrapy.Field()
    # 公布/执行单位
    publish_unit = scrapy.Field()
    # 创建日期
    create_date = scrapy.Field()
    # 更新日期
    update_date = scrapy.Field()
