import argparse
from datetime import datetime, timedelta


def calc_financial_freedom(current_amount, monthly_saving, annual_return_rate, target_amount):
    start_date = datetime.today()
    current_money = current_amount
    r = annual_return_rate / 100
    month_rate = (1 + r) ** (1 / 12) - 1

    date = start_date
    months = 0

    while current_money < target_amount:
        current_money *= (1 + month_rate)
        current_money += monthly_saving
        months += 1
        date += timedelta(days=30)

    delta = date - start_date
    total_days = delta.days
    years = total_days // 365
    remaining_days = total_days % 365
    months_approx = remaining_days // 30
    days = remaining_days % 30

    print("\n财富自由模拟结果：")
    print(f"达成目标日期：{date.date()}")
    print(f"还需时间：{years} 年 {months_approx} 个月 {days} 天")
    print(f"届时总资产约为：{current_money:,.2f} 元")


if __name__ == "__main__":
    # python free_calculator.py -now 630000 -save 23000 -ratio 12 -gold 5280000
    parser = argparse.ArgumentParser(description="财富自由计算器")
    parser.add_argument("-now", type=float, required=True, help="当前资金")
    parser.add_argument("-save", type=float, required=True, help="每月储蓄金额")
    parser.add_argument("-ratio", type=float, required=True, help="年化复合收益率（单位：百分数）")
    parser.add_argument("-gold", type=float, required=True, help="财富自由目标金额")

    args = parser.parse_args()

    calc_financial_freedom(
        current_amount=args.now,
        monthly_saving=args.save,
        annual_return_rate=args.ratio,
        target_amount=args.gold
    )
