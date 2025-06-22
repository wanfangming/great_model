# -*- coding: utf-8 -*-
# @日期    : 2021/6/20 9:44
# @作者  : 万方名
# @FileName: 未来基金_V6.py


import time
import requests
import argparse
import threading
import pandas as pd
import akshare as ak

from bs4 import BeautifulSoup
from operator import itemgetter

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


def parse_data(data, stock_code, hongkong):
    parsed_data = BeautifulSoup(data, 'html5lib')
    scripts = parsed_data.select('script')
    # gold_script = str(scripts[13])
    if hongkong == '港':
        current_price = ak.stock_hk_hist(stock_code)['收盘'].values[-1]
    else:
    # 获取当前价格
        stock_bid_ask_em_df = ak.stock_bid_ask_em(stock_code)
        current_price = \
        stock_bid_ask_em_df.loc[stock_bid_ask_em_df['item'] == '最新']['value'].reset_index(drop=True)[0]

    return float(current_price)


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
        if current_price * 0.9 < supplement_point:
            may_break_supplement_point_list.append([stock_name, current_price, supplement_point])
        if current_price * 1.1 > sale_point and bought_times > 1:
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
    print('-' * 15)
    print('跌停可到补点：')
    for item in may_break_supplement_point_list:
        item.append((item[1] - item[2]) / item[1])
    may_break_supplement_point_list_sorted = sorted(may_break_supplement_point_list, key=itemgetter(3), reverse=True)
    for item in may_break_supplement_point_list_sorted:

        print(f'{item[0]} 离补点 {"%.2f" % (item[3] * 100)}%， 补点：{"%.2f" % item[2]}')
    print('-' * 15)

    print('涨停可到卖点：')
    for item in may_break_sale_point_list:
        item.append((item[2] - item[1]) / item[1])
    may_break_sale_point_list_sorted = sorted(may_break_sale_point_list, key=itemgetter(5))
    for item in may_break_sale_point_list_sorted:
        print(
            f'{item[0]} 离卖点 {"%.2f" % (item[5] * 100)}%， 卖点：{"%.2f" % item[2]}，最后一手赚了{int(item[3])}（{"%.2f" % item[4]}%）')

    print('-' * 15)
    print('已涨到卖点：')
    for item in break_sale_point_list:
        print(f'{item[0]} 已涨到卖点，现价：{item[1]}，卖点： {"%.2f" % item[2]}')

    print('-' * 15)
    print('已跌破补点：')
    for item in break_supplement_point_list:
        item.append((item[2] - item[1]) / item[1])
    break_supplement_point_list_sorted = sorted(break_supplement_point_list, key=itemgetter(2), reverse=True)
    for item in break_supplement_point_list_sorted:
        print(f'{item[0]} 已跌破补点 {"%.2f" % (item[3] * 100)}%， 补点：{"%.2f" % item[2]}')
    print('-' * 15)


def process_(bought_times, stock_code, buy_point, buy_price, iter_percent, hongkong, stock_name):
    data = get_data(stock_code)
    current_price_price = parse_data(data, stock_code, hongkong)

    list_processor(bought_times, current_price_price, buy_point, stock_name, buy_price, iter_percent)


def main():
    parser = argparse.ArgumentParser()

    # 字符串参数
    parser.add_argument('-data', default='../data/股票代码.xlsx')
    args = parser.parse_args()

    # 开始计总消耗时间
    start = time.time()

    # 读取股票买点、卖点等信息
    code_csv_path = args.data
    code_df = pd.read_excel(code_csv_path)

    # 制作线程池、每个线程所需的信息和每个线程所执行的函数
    t_list = []
    for index in range(len(code_df)):
        bought_times = float(code_df['买入次数'][index])
        hongkong  = code_df['港股'][index]

        stock_code = str(code_df['股票代码'][index])
        if hongkong == '港':
            if len(stock_code) < 5:
                stock_code = '0' * (5 - len(stock_code)) + stock_code
        else:
            if len(stock_code) < 6:
                stock_code = '0' * (6 - len(stock_code)) + stock_code

            buy_point = code_df['买点'][index]
        buy_price = code_df['买入价格'][index]
        iter_percent = code_df['迭代比例'][index]
        stock_name  = code_df['公司名称'][index]

        # process_(bought_times, stock_code, buy_point, buy_price)
        t = MyThread(process_, (bought_times, stock_code, buy_point, buy_price, iter_percent, hongkong, stock_name))
        t_list.append(t)
        t.start()

    for t in t_list:
        t.join()  # 一定要join，不然主线程比子线程跑的快，会拿不到结果

    # 屏幕打印
    print()
    printer()
    print(f'处理{len(code_df)}支股票花费{time.time() - start}秒。')


if __name__ == '__main__':
    main()
