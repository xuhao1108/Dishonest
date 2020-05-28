# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


import pymysql
from Dishonest.settings import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE


class DishonestPipeline(object):
    def __init__(self):
        self.mysql = pymysql.Connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASSWORD,
                                     database=MYSQL_DATABASE)
        self.cursor = self.mysql.cursor()

    def process_item(self, item, spider):
        # 若年龄为0，则表示为企业
        if item['age'] == 0:
            is_exist_sql = 'SELECT * FROM dishonest WHERE name = %s;'
            params = [item['name']]
        else:
            is_exist_sql = 'SELECT * FROM dishonest WHERE name = %s AND card_num = %s;'
            # 如果身份证号码为加密，则将后7位到后4位替换为****
            if len(item['card_num']) == 18:
                item['card_num'] = item['card_num'][:-7] + '****' + item['card_num'][-4:]
            params = [item['name'], item['card_num']]
        # 执行查询信息
        self.cursor.execute(is_exist_sql, params)
        # 判断查询结果
        if self.cursor.fetchone():
            pass
            # print("已存在该信息：{}".format(dict(item['name'])))
        else:
            # 将item转换为key，value
            key, value = zip(*dict(item).items())
            # 拼接sql语句
            insert_sql = 'INSERT INTO dishonest({}) VALUES({});'.format(",".join(key), ",".join(['%s'] * len(value)))
            # 执行sql语句
            self.cursor.execute(insert_sql, value)
            # 提交
            self.mysql.commit()
        return item

    def __del__(self):
        # 关闭游标
        self.cursor.close()
        # 关闭数据库
        self.mysql.close()
