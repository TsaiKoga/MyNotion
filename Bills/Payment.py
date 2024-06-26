import requests
import json
import os
import hashlib
import arrow
import csv
import regex
from dotenv import load_dotenv

load_dotenv()

class Payment:
    def __init__(self):
        """
        Notion 环境变量
        :param
        :return
        """
        self.access_token = os.getenv('BILL_NOTION_SECRET')
        self.database_id  = os.getenv('BILL_NOTION_DATABASE_ID')

    def is_bill_in_notion(self, trade_no):
        """
        订单是否已在Notion数据库中
        :param trade_no 订单号
        :return
        """
        url          = 'https://api.notion.com/v1/databases/' + str(self.database_id) + '/query'
        query_data         = {
            "filter": {
                "property": "交易订单号",
                "rich_text": {"equals": trade_no}
            }
        }
        data = json.dumps(query_data)
        result = requests.post(url, headers={'Content-Type':'application/json',
               'Authorization': 'Bearer {}'.format(self.access_token),
               'Notion-Version': '2022-06-28'}, data=data)
        result = result.json()
        print('结果:')
        print(result)
        if not result['results']:
            return False
        else:
            return True

    def notion_insert_database(self, data):
        """
        插入 notion 表格
        :param data 数据
        :return
        """
        url  = 'https://api.notion.com/v1/pages/'
        result = requests.post(url, headers={'Content-Type':'application/json',
                       'Authorization': 'Bearer {}'.format(self.access_token),
                       'Notion-Version': '2022-06-28'}, data=data)
        print(result.json())

    def build_properties(self, exchanged_at, exchange_date, exchange_type, trade_no, content, price, income_type, platform):
        """
        构建 notion 插入数据
        :param exchanged_at 交易时间
        :param exchange_date 交易日期
        :param exchange_type 交易类型
        :param trade_no 订单号
        :param content 交易内容
        :param price 交易价格
        :param income_type 收支类型
        :param platform 平台(微信/支付宝)
        :return
        """
        body = {
            "parent": {"database_id": self.database_id},
            "properties": {
                "交易订单号": {
                    "rich_text": [{
                        "text": {
                            "content": trade_no
                        }
                    }]
                },
                "交易时间": { "type": "date", "date": { "start": exchanged_at} },
                "年月": {
                    "select": {
                        "name": exchange_date
                    }
                },
                "交易类型": {
                    "select": {
                        "name": exchange_type
                    }
                },
                "金额": { "type": "number", "number": float(price) },
                "平台": {
                    "select": {
                        "name": platform
                    }
                }
            }
        }
        return json.dumps(body)


    def wechat(self, filepath):
        """
        读取微信 csv 插入
        :param filepath 微信账单文件地址
        :return
        """
        with open(filepath, "r", encoding="utf-8-sig", newline="") as f:
            lines = f.readlines()
            striped_lines = []
            start = False
            for line in lines:
                if not start:
                    if line.startswith("----------------------"):
                        start = True
                    continue
                striped_lines.append(line.strip())

            csvreader = csv.DictReader(striped_lines)
            for row in csvreader:
                trade_no = hashlib.md5(row['交易单号'].encode('utf-8')).hexdigest()
                exchanged_at = arrow.get(row["交易时间"]).replace(tzinfo="+08").datetime
                content = row["商品"] + "，" + row["交易类型"] + "，" + row["交易对方"]
                price = row["金额(元)"]
                income_type = row["收/支"]
                exchange_type = row["交易类型"]
                exchange_date = exchanged_at.strftime("%Y-%m")
                print(trade_no, income_type, exchanged_at, content, price, exchange_type)
                if income_type == "收入":
                    price = price[1:]
                elif income_type == "支出":
                    price = "-" + price[1:]
                else:
                    print("[未被计入]")
                    continue
                properties = self.build_properties(exchanged_at.strftime("%Y-%m-%d %H:%M:%S"), exchange_date, exchange_type, trade_no, content, price, income_type, "微信")
                if (self.is_bill_in_notion(trade_no)):
                    continue
                self.notion_insert_database(properties)

    def alipay(self, filepath):
        """
        读取支付宝 csv 插入
        :param filepath 支付宝账单文件地址
        :return
        """
        with open(filepath, "r", encoding="gbk", newline="") as f:
            lines = f.readlines()
            striped_lines = []
            start = False
            for line in lines:
                if not start:
                    if line.startswith("------------------------支"):
                        start = True
                    continue
                if line.startswith("------------------------支"):
                    break
                l = regex.sub(r"\s+,", ",", line)
                striped_lines.append(l)

            csvreader = csv.DictReader(striped_lines)
            for row in csvreader:
                print(row)
                trade_no = hashlib.md5(row['交易订单号'].encode('utf-8')).hexdigest()
                exchanged_at = arrow.get(row["交易时间"]).replace(tzinfo="+08").datetime
                exchange_date = exchanged_at.strftime("%Y-%m")
                content = row["商品说明"] + "，" + row["交易对方"]
                price = row["金额"]
                income_type = row["收/支"]
                exchange_type = row["交易分类"]
                print(exchanged_at, content, price, income_type)
                if price == "0":
                    print("[未被计入]")
                    continue
                elif income_type == "收入" or income_type == "解冻":
                    price = price
                elif income_type == "支出" or income_type == "冻结":
                    price = "-" + price
                else:
                    print("[未被计入]")
                    continue
                properties = self.build_properties(exchanged_at.strftime("%Y-%m-%d %H:%M:%S"), exchange_date, exchange_type, trade_no, content, price, income_type, "支付宝")
                if (self.is_bill_in_notion(trade_no)):
                    continue
                self.notion_insert_database(properties)


if __name__ == '__main__':
    payment = Payment()
    wechat_filepath = os.getenv('WECHAT_FILEPATH')
    alipay_filepath = os.getenv('ALIPAY_FILEPATH')
    payment.wechat(wechat_filepath)
    payment.alipay(alipay_filepath)
