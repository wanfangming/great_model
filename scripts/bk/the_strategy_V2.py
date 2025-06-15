import sys
import copy
import datetime
import akshare as ak


class the_strategy:
    def __init__(self):
        # 初始化一些基本数据
        self.MAX_SPEND = 0.  # 最高投资金额
        self.NET_INCOME = 0.  # 净收入
        self.FLOATING_PROFIT = 0.  # 浮盈
        self.REMAINING = 100  # 股票剩余数量
        self.COST = 0.  # 成本价
        self.NIR = 0.0  # 净收益率
        self.FIR = 0.0  # 浮动收益率
        self.buy_point = 99999  # 初始化买点，暂时没想到比较好的值，以后改一下

        self.one_day = datetime.timedelta(days=1)
        self.zh_sina_index_stock_hist_url = "https://finance.sina.com.cn/realstock/company/{}/hisdata/klc_kl.js"

    def update_sale_point(self):
        self.sale_point = self.buy_price * (
                1 + 2.0 * self.iter_percent) if self.bought_times == 1 else self.buy_price * (
                1 - (self.bought_times - 2) * self.iter_percent)

    def skip_weekend(self, day):
        day_list = day.split('-')
        year = int(day_list[0])
        month = int(day_list[1])
        d = int(day_list[2])
        day = datetime.date(year, month, d)
        if datetime.date.isoweekday(day) in [6, 7]:
            day += datetime.timedelta(days=1)
            self.skip_weekend(str(day))

        return str(day)

    def load_stock_data(self):
        # 获取线上数据，删除不需要的列
        return ak.stock_zh_a_hist(symbol=self.code, period="daily", start_date=self.start_day, end_date=self.end_day,
                                  adjust="qfq")

    def init_dynamic_variable(self):
        try:
            buy_price = self.stock_data['开盘'][0]
        except:
            print('输入的时间有误，请重新输入！')
            exit()
        recent_buy_price = self.stock_data['开盘'][0]
        self.MAX_SPEND = buy_price * 100.

        investment = buy_price * 100.
        sale_point = buy_price * (1 + self.iter_percent * 2)
        supplement_point = buy_price * (1 - self.iter_percent)
        cost = self.stock_data['开盘'][0]
        return buy_price, recent_buy_price, investment, sale_point, supplement_point, 1, cost

    def load_lists(self):
        return list(self.stock_data['开盘'].values), list(self.stock_data['最高'].values), list(
            self.stock_data['最低'].values), list(self.stock_data['收盘'].values), list(self.stock_data['日期'])

    def printer(self, stock_name, iter_percent):
        print(f'{stock_name}, 迭代点数%{int(iter_percent * 100)}, {self.TRADING_DAYS_NUM} 个交易日：')
        print('最大花费：{:.2f}'.format(self.MAX_SPEND))
        print('净收入：{:.2f}'.format(self.NET_INCOME))
        print('浮盈：{:.2f}'.format(self.FLOATING_PROFIT))
        print('目前剩余 {} 股, 第一手买入价：{:.2f}。\n'.format(self.REMAINING, self.buy_price))
        print('净收益率：{:.2f}%'.format(self.NIR * 100))
        print('浮动收益率：{:.2f}%'.format(self.FIR * 100))

    def calculate(self, stock_name, code, iter_percent, start_day, end_day):
        # 初始化参数
        self.code = code
        self.iter_percent = iter_percent
        self.start_day = start_day
        self.end_day = end_day

        # 获取需要的数据段
        self.stock_data = self.load_stock_data()

        # 初始化最初买入价等动态变量
        self.buy_price, self.recent_buy_price, self.investment, self.sale_point, self.supplement_point, self.bought_times, self.COST = self.init_dynamic_variable()

        open_list, high_list, low_list, close_list, date_list = self.load_lists()
        self.TRADING_DAYS_NUM = len(open_list)  # 交易日数量
        # 开始主循环
        for o, high, low, close, date in zip(open_list, high_list, low_list, close_list, date_list):
            if self.REMAINING > 0:
                if high >= self.sale_point:  # 如果达到卖点
                    self.REMAINING -= 100
                    if self.bought_times == 1:
                        self.NET_INCOME += (self.buy_price * 100 * self.iter_percent * 2)
                    else:
                        self.NET_INCOME += (self.buy_price * 100 * self.iter_percent)

                    self.investment -= self.sale_point * 100
                    self.bought_times -= 1
                    if self.REMAINING == 0.:
                        self.buy_point = self.buy_price * 1.05
                    else:
                        self.update_sale_point()  # 更新卖点
                        self.supplement_point = self.buy_price * (1 - self.bought_times * self.iter_percent)

                if low <= self.supplement_point:  # 如果到达补点
                    self.investment += self.supplement_point * 100
                    self.REMAINING += 100
                    self.COST = (self.COST * self.bought_times + self.supplement_point) / (self.bought_times + 1)

                    self.bought_times += 1
                    self.recent_buy_price = copy.copy(self.supplement_point)
                    self.supplement_point = self.buy_price * (1 - self.bought_times * self.iter_percent)
                    # 更新卖点
                    self.update_sale_point()

                    if self.investment > self.MAX_SPEND:
                        self.MAX_SPEND = copy.copy(self.investment)

            # 手上没有并且跌破买点的情况
            elif low <= self.buy_point:
                self.REMAINING += 100
                self.investment += self.buy_point * 100
                self.bought_times = 1
                self.supplement_point = self.buy_point * (1 - self.bought_times * self.iter_percent)
                self.COST = copy.copy(self.buy_point)
                self.recent_buy_price = copy.copy(self.buy_point)
                # 更新卖点
                self.update_sale_point()
                if self.investment > self.MAX_SPEND:
                    self.MAX_SPEND = copy.copy(self.investment)

        self.COST = self.buy_price - (self.bought_times - 1) * self.iter_percent / 2 * self.buy_price

        self.FLOATING_PROFIT = self.REMAINING * close - self.REMAINING * self.COST + self.NET_INCOME

        # 计算净收益率和浮动收益率
        self.NIR = self.NET_INCOME / self.MAX_SPEND / len(open_list) * 365.
        self.FIR = self.FLOATING_PROFIT / self.MAX_SPEND / len(open_list) * 365.
        self.printer(stock_name, iter_percent)
        print('-' * 15)


def main():


    # 没有输入具体点数的情况
    if len(sys.argv) == 5:
        start_day = '20' + str(sys.argv[1])
        end_day = '20' + str(sys.argv[2])
        point = float(sys.argv[3]) / 100
        stock_name = sys.argv[4]
        name_df = ak.stock_zh_a_spot_em()
        try:
            stock_code = name_df[name_df['名称'] == stock_name]['代码'].values[0]
        except:
            print(f'股票名称{stock_name}输入错误，请重新输入！')
            exit()
        # 实例化
        strategy = the_strategy()
        strategy.calculate(stock_name, stock_code, point, start_day, end_day)

    # 输入了具体点数的情况
    elif len(sys.argv) == 4:
        iters = [0.1, 0.09, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03, 0.02, 0.01]
        start_day = '20' + str(sys.argv[1])
        end_day = '20' + str(sys.argv[2])
        stock_name = sys.argv[3]
        name_df = ak.stock_zh_a_spot_em()
        try:
            stock_code = name_df[name_df['名称'] == stock_name]['代码'].values[0]
        except:
            print(f'股票名称{stock_name}输入错误，请重新输入！')
            exit()
        for point in iters:
            # 实例化
            strategy = the_strategy()
            strategy.calculate(stock_name, stock_code, point, start_day, end_day)
    # 其他情况
    else:
        print(
            '输入格式有误！正确格式为：\n1. python the_strategy_V2.py 美的集团 220101 220301 3\n2. python the_strategy_V2.py \
            美的集团 220101 220301')


if __name__ == '__main__':
    # 格式样例：
    # 1. python the_strategy_V2.py 220101 220301 3 美的集团
    # 2. python the_strategy_V2.py 220101 220301 美的集团
    main()
