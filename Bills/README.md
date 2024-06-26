# Notion 账单


## 预备工作

新建 Page 并创建 Notion 数据库

创建 [Notion API](https://www.notion.so/my-integrations)

创建数据库连接 「Add connections」

获取数据库 DATABASE_ID

创建 .env 文件,将 `database_id` 与 创建API的 `token` 写入该文件
```bash
BILL_NOTION_DATABASE_ID=
BILL_NOTION_SECRET=
```

从微信,支付宝导出个人账单,并将路径写入 .env 文件
```bash
WECHAT_FILEPATH=
ALIPAY_FILEPATH=
```




## 运行账单脚本

```
python Payment.py
```


