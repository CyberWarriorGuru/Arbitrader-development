# STEP 1: pip install plotly python-binance pandas
# STEP 2: Populate your API key and secret below
# !!! WARNING This has been untested. Use at your own risk !!!

import pdb

import px as px
from binance.client import Client

import pandas as pd
import numpy as np

# import plotly.express as px

from django.conf import settings

api_key = settings.BINANCE_API_KEY
api_secret = settings.BINANCE_SECRET_KEY

client = Client(api_key, api_secret)

symbol1 = "BCHBTC"
symbol2 = "BCHUSDT"
symbol3 = "BTCUSDT"
from_date = "01 Oct, 2019"
to_date = "30 Sep, 2020"

# define algorithm variables
current_balance = 2
starting_capital = 2
rolling_window = 20
sell_periods = 1
z_score_buy_threshold = -1.5
z_score_short_threshold = 1.5
transaction_fee = 0  # 0.0750 / 100


# pull and format data
def get_data(symbol):
    candles = client.get_historical_klines(
        symbol, Client.KLINE_INTERVAL_1HOUR, from_date, to_date
    )
    df_ticker = pd.DataFrame(candles)
    df_ticker = df_ticker.iloc[:, [0, 4]]
    df_ticker[0] = df_ticker[0] / 1000
    df_ticker[0] = pd.to_datetime(df_ticker[0], unit="s")
    df_ticker.columns = ["Date", symbol]
    df_ticker = df_ticker.set_index("Date")
    return df_ticker


# Get datasets
dt_1 = get_data(symbol1)
dt_2 = get_data(symbol2)
dt_3 = get_data(symbol3)


# Combine symbol 1 with symbol 2
df_ticker_main = dt_1.join(dt_2)

# Combine symbol 1 with symbol 2 and join with symbol 3
df_ticker_main = df_ticker_main.join(dt_3)

# Drop the columns that have missing values.
df_ticker_main = df_ticker_main.dropna()

#
df_ticker_main = df_ticker_main.astype(float)

# calculate z score
df_ticker_main[symbol2 + "_Log"] = np.log(df_ticker_main[symbol2])
df_ticker_main[symbol3 + "_Log"] = np.log(df_ticker_main[symbol3])
df_ticker_main["Distance"] = (
    df_ticker_main[symbol2 + "_Log"] - df_ticker_main[symbol3 + "_Log"]
)
df_ticker_main["Mean_Dist"] = (
    df_ticker_main["Distance"].rolling(rolling_window).mean()
)
df_ticker_main["Std_Dist"] = (
    df_ticker_main["Distance"].rolling(rolling_window).std()
)
df_ticker_main["z_score"] = (
    df_ticker_main["Distance"] - df_ticker_main["Mean_Dist"]
) / df_ticker_main["Std_Dist"]

# save table to csv
df_ticker_main.to_csv("pair.csv")
index_length = len(df_ticker_main)

# determine trades
open_orders = 0
net_return = 0
net_change = 0
buy_price = 0
short_price = 0
counts = 0
time_period = 0
sell_price = 0

balance_list = []
returns_list = []

for index, row in df_ticker_main.iterrows():
    current_price = row[symbol1]
    z_score = row["z_score"]

    # stop when balance reduces and
    if current_balance > 0.1 and counts < (index_length - sell_periods):

        # close any open buy positions
        if open_orders == 1 and counts == time_period:
            sell_price = current_price
            net_return = sell_price / buy_price
            net_change = (sell_price - buy_price) / buy_price
            current_balance = (
                current_balance * (1 - transaction_fee) * net_return
            )
            returns_list.append(net_change)
            open_orders = 0

        # close any open short positions
        if open_orders == 2 and counts == time_period:
            sell_price = current_price
            net_return = short_price / sell_price
            net_change = (short_price - sell_price) / short_price
            current_balance = (
                current_balance * (1 - transaction_fee) * net_return
            )
            returns_list.append(net_change)
            open_orders = 0

        # calculate buy's
        if open_orders == 0 and z_score <= z_score_buy_threshold:
            buy_price = current_price
            open_orders = 1
            time_period = counts + sell_periods

        # calculate shorts's
        if open_orders == 0 and z_score >= z_score_short_threshold:
            short_price = current_price
            open_orders = 2
            time_period = counts + sell_periods

        # print trade information
        print(
            counts,
            "Balance " + str(current_balance),
            "Buy Price " + str(buy_price),
            "Sell Price " + str(sell_price),
            "Net Return " + str(net_return),
        )

    # increment index
    balance_list.append(current_balance)

    counts += 1

# calculate Sharpe Ratio
mean_return = np.average(returns_list)
std_return = np.std(returns_list)
sharpe_ratio = mean_return / std_return
sharpe_ratio_annual = np.sqrt(365) * sharpe_ratio

# print results
print("")
print("Annual Sharpe Ratio", round(sharpe_ratio_annual, 2))
print("Current Balance", round(current_balance, 2))
print("Starting Balance", round(starting_capital, 2))
print("Net Return", round(current_balance / starting_capital, 2))

# plot symbol 2
fig = px.line(df_ticker_main[symbol2])
fig.show()

# plot symbol 3
fig = px.line(df_ticker_main[symbol3])
fig.show()

# plot z-score
fig = px.line(df_ticker_main["z_score"])
fig.show()

# plot balance
fig = px.line(balance_list)
fig.show()
