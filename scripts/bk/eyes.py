# -*- coding: utf-8 -*-
"""
@Time ： 2023/5/10 13:46
@Auth ： WanFangming
@File ：eyes.py
"""

import re
import time
import smtplib
import requests
import threading
import pandas as pd

from bs4 import BeautifulSoup
from operator import itemgetter
from email.utils import formataddr
from email.mime.text import MIMEText

stock_name_list = []
value_list = []
dividend_rate_list = []
current_price_list = []
PER_list = []
buy_point_list = []
point_buy_ratio_list = []
change_ratio_list = []
bought_ratio_list = []
wfm_earnings_list = []
wfc_earnings_list = []
point_sell_ratio_list = []
second_buy_price_list = []
thrid_buy_price_list = []
fourth_buy_price_list = []
fifth_buy_price_list = []

# 到达补点的list [stock_name, current_price, supplement_point]
break_supplement_point_list = []

break_sale_point_list = []  # 到达卖点

# 到达补点的list [stock_name, current_price, buy_point]
break_buy_point_list = []

may_break_supplement_point_list = []  # 跌停可到补点
may_break_sale_point_list = []  # 跌停可到卖点
may_break_buy_point_list = []  # 跌停可到买点


class MyThread(threading.Thread):
    def __init__(self, func, args=()):
        super(MyThread, self).__init__()
        self.func = func
        self.args = args

    def run(self):
        self.result = self.func(*self.args)

    def get_result(self):
        try:
            return self.result  # 如果子线程不使用join方法，此处可能会报没有self.result的错误
        except Exception:
            return None


def get_data(stock_code):
    url_sz = 'https://xueqiu.com/S/SZ{}'.format(stock_code)
    url_sh = 'https://xueqiu.com/S/SH{}'.format(stock_code)

    # 获取方法F12
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36 Edg/87.0.664.57"
    }

    response = requests.get(url_sz, headers=headers)
    if response.status_code == 404:
        response = requests.get(url_sh, headers=headers)
    return response.text


def parse_data(data):
    parsed_data = BeautifulSoup(data, 'html5lib')
    scripts = parsed_data.select('script')
    gold_script = str(scripts[13])
    # 获取股票名
    stock_name = parsed_data.title.string[:parsed_data.title.string.find('股票股价')]

    # 获取当前价格
    current_price_start = re.search('current"', gold_script, flags=0).span()[0]
    str_current_price = gold_script[current_price_start:current_price_start + 20]
    current_price = re.sub(r'[^0-9.]', '', str_current_price)

    return stock_name, float(current_price)


def list_processor(bought_times, current_price, buy_point, stock_name, buy_price, iter_percent):
    # 1.没买的股票
    if bought_times == 0:
        if current_price < buy_point:
            break_buy_point_list.append([stock_name, current_price, buy_point])
        elif (current_price * 0.9) <= buy_point:
            may_break_buy_point_list.append([stock_name, current_price, buy_point])
    # 2.买过的股票
    else:
        # 计算卖点
        sale_point = buy_price * (1 + 2.0 * iter_percent) if bought_times == 1 else buy_price * (
                1 - (bought_times - 2) * iter_percent)

        # 计算补点（覆盖10个点和5个点的情况）
        supplement_point = buy_price * (1 - bought_times * iter_percent)

        # 计算最后一手赚了多少
        last_price = buy_price - buy_price * iter_percent * (bought_times - 1)
        gain_value = (current_price - last_price) * 100
        gain_percent = (current_price - last_price) / last_price * 100

        if current_price > sale_point:
            break_sale_point_list.append([stock_name, current_price, sale_point])
        elif current_price < supplement_point:
            break_supplement_point_list.append([stock_name, current_price, supplement_point])
        if current_price < 1.01 * supplement_point:
            may_break_supplement_point_list.append([stock_name, current_price, supplement_point])
        if current_price * 1.01 > sale_point:
            may_break_sale_point_list.append([stock_name, current_price, sale_point, gain_value, gain_percent])


def calculate_value(current_price, buy_point):
    # 离买点的百分比
    percentage_from_buy_point = (current_price - buy_point) / current_price
    return percentage_from_buy_point


def process_bought_ratio(x):
    if not (x > 0) and not (x < 0):
        return ''
    return format(x, '.2%')


def printer():
    # print('已跌破买点：')
    # for item in break_buy_point_list:
    #     item.append((item[2] - item[1]) / item[1])
    # break_buy_point_list_sorted = sorted(break_buy_point_list, key=itemgetter(3), reverse=True)
    # for item in break_buy_point_list_sorted:
    #     print(f'{item[0]} 已跌破买点 {"%.2f" % (item[3] * 100)}%， 买点： {item[2]}')
    # print('-' * 15)

    # print('跌停可到买点：')
    # for item in may_break_buy_point_list:
    #     item.append((item[1] - item[2]) / item[1])
    #     item.append(())
    # may_break_buy_point_list_sorted = sorted(may_break_buy_point_list, key=itemgetter(3))
    # for item in may_break_buy_point_list_sorted:
    #     print(f'{item[0]} 离买点 {"%.2f" % (item[3] * 100)}%， 买点：{item[2]}')

    # print('-' * 15)

    email_text = '存在股票在一个点之内需要交易，请立即登录账户查看！'
    receivers = ['1393852116@qq.com', '543196482@qq.com']  # 接收人邮箱账号（可以多个，逗号隔开）

    # print('跌一个点可到补点：')
    for item in may_break_supplement_point_list:
        item.append((item[1] - item[2]) / item[1])
    may_break_supplement_point_list_sorted = sorted(may_break_supplement_point_list, key=itemgetter(3), reverse=True)
    for item in may_break_supplement_point_list_sorted:
        # print(f'{item[0]} 离补点 {"%.2f" % (item[3] * 100)}%， 补点：{"%.2f" % item[2]}')
        send_email(email_text, receivers)
        exit()
    # print('-' * 15)

    # print('涨一个点可到卖点：')
    for item in may_break_sale_point_list:
        item.append((item[2] - item[1]) / item[1])
    may_break_sale_point_list_sorted = sorted(may_break_sale_point_list, key=itemgetter(3))
    for item in may_break_sale_point_list_sorted:
        # print(
        #     f'{item[0]} 离卖点 {"%.2f" % (item[5] * 100)}%， 卖点：{"%.2f" % item[2]}，最后一手赚了{int(item[3])}（{"%.2f" % item[4]}%）')
        send_email(email_text, receivers)
        exit()
    # print('-' * 15)
    # print('已涨到卖点：')
    for item in break_sale_point_list:
        # print(f'{item[0]} 已涨到卖点，现价：{item[1]}，卖点： {item[2]}')
        send_email(email_text, receivers)
        exit()

    # print('-' * 15)
    # print('已跌破补点：')
    for item in break_supplement_point_list:
        item.append((item[2] - item[1]) / item[1])
    break_supplement_point_list_sorted = sorted(break_supplement_point_list, key=itemgetter(2), reverse=True)
    for item in break_supplement_point_list_sorted:
        # print(f'{item[0]} 已跌破补点 {"%.2f" % (item[3] * 100)}%， 补点：{item[2]}')
        send_email(email_text, receivers)
        exit()
    # print('-' * 15)


def send_email(text, receivers):
    host = 'smtp.qq.com'  # 发件人邮箱的SMTP服务器
    sender = '1393852116@qq.com'  # 发件人邮箱账号
    password = 'viuhohzfodlughii'  # 发件人邮箱密码（不是qq密码，通过设置--》账户--》开启--》授权码）

    msg = MIMEText(text, 'plain', 'utf-8')  # 邮件正文的内容、设置文本格式：plain、设置编码格式：utf-8
    msg['From'] = formataddr(['万方名', sender])  # 发件人邮箱昵称、发件人邮箱账号
    msg['To'] = formataddr(['wwww', ','.join(receivers)])  # 收件人邮箱昵称、收件人邮箱账号
    msg['Subject'] = "存在股票在一个点之内需要交易，请立即登录账户查看！"  # 邮件主题
    try:
        # 创建并登录SMTP服务器
        server = smtplib.SMTP_SSL(host, 465)  # 创建一个STMP对象，SSL加密(也可选择明文发送server = smtplib.SMTP(host, 25))
        server.login(sender, password)  # 登陆需要认证的SMTP服务器（发件人邮箱账号、密码）
        # 发送邮件
        server.sendmail(sender, receivers,
                        msg.as_string())  # 发件人邮箱账号、收件人邮箱账号、发送邮件内容，as_string()是将msg(MIMEText对象或者MIMEMultipart对象)变为str
        server.quit()  # 断开STMP服务器链接
        print('邮件发送成功！')
    except smtplib.SMTPException as e:
        print('Error: 邮件发送失败！', e)


def process_(bought_times, stock_code, buy_point, buy_price, iter_percent):
    data = get_data(stock_code)
    stock_name, current_price_price = parse_data(data)

    list_processor(bought_times, current_price_price, buy_point, stock_name, buy_price, iter_percent)


def main():
    detection_num = 1
    while True:
        # 读取股票买点、卖点等信息
        code_csv_path = './股票代码.xlsx'
        code_df = pd.read_excel(code_csv_path)
        # 制作线程池、每个线程所需的信息和每个线程所执行的函数
        t_list = []
        for index in range(len(code_df)):
            bought_times = float(code_df['买入次数'][index])

            stock_code = str(code_df['股票代码'][index])
            if len(stock_code) < 6:
                stock_code = '0' * (6 - len(stock_code)) + stock_code
            buy_point = code_df['买点'][index]
            buy_price = code_df['买入价格'][index]
            iter_percent = code_df['迭代比例'][index]

            # process_(bought_times, stock_code, buy_point, buy_price)
            t = MyThread(process_, (bought_times, stock_code, buy_point, buy_price, iter_percent))
            t_list.append(t)
            t.start()

        for t in t_list:
            t.join()  # 一定要join，不然主线程比子线程跑的快，会拿不到结果

        print(f'已检测{detection_num}次...')
        printer()
        detection_num += 1
        time.sleep(20)

        # if may_break_supplement_point_list or may_break_sale_point_list or break_supplement_point_list or break_sale_point_list:
        #     email_text = '存在股票在一个点之内需要交易，请立即登录账户查看！'
        #     receivers = ['1393852116@qq.com', '543196482@qq.com']  # 接收人邮箱账号（可以多个，逗号隔开）
        #     send_email(email_text, receivers)
        #     exit()
        # else:
        #     time.sleep(10)
        #     may_break_supplement_point_list, may_break_sale_point_list, break_supplement_point_list, break_sale_point_list = [], [], [], []


if __name__ == '__main__':
    main()
