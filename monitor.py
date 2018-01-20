import numpy as np
import requests
import time

class Monitor:

    def __init__(self):
        self.coins = self.setup()
        print("finished init")

    class Coin:
        def __init__(self, name, market):
            self.name = name
            self.market = market
            self.volume_median24h = 0
            self.prev_volume = 0
            self.prev_price = 0
            self.rsi_down = False
            self.ema_increasing = False
            self.macd_increasing = False

    def setup(self):
        api_response = requests.get('https://poloniex.com/public?command=returnTicker').json()
        tickers = []
        print("after first request")
        for key, value in api_response.items():
            pair = key.split('_')
            market, coin_name = pair[0], pair[1]
            if market == "BTC" or market == "USDT":
                tickers.append(self.Coin(coin_name, market))

        current_time = time.time()
        for coin in tickers:
            url = "https://poloniex.com/public?command=returnChartData&currencyPair=" + coin.market + '_' + coin.name +\
                      "&start=" + str(current_time - 11520) + "&end=" + "9999999999" + "&period=" + "900"

            api_response = requests.get(url).json()

            volumes = []
            for candle in api_response:
                volume = float(candle["volume"])
                volumes.append(volume)

            volumes_np = np.array(volumes)
            median_volume = np.average(volumes_np)
            coin.volume_median24h = median_volume

        return tickers

    def sma(self, period, closep=None):
        # if closep is None:
        #     current_time = time.time()
        #     url = "https://poloniex.com/public?command=returnChartData&currencyPair=USDT_" + ticker + "&start=" + \
        #           str(current_time - 86000) + "&end=" + "9999999999" + "&period=" + "300"
        #
        #     print(url)
        #     api_response = requests.get(url).json()
        #
        #     closep = []
        #     for candle in api_response:
        #         price = float(candle["close"])
        #         closep.append(price)

        closep = np.array(closep)
        weigths = np.repeat(1.0, period) / period
        smas = np.convolve(closep, weigths, 'valid')

        return smas

    def ema(self, period, closep=None):
        # if closep is None:
        #     current_time = time.time()
        #     url = "https://poloniex.com/public?command=returnChartData&currencyPair=USDT_" + ticker + "&start=" + \
        #           str(current_time - 86000) + "&end=" + "9999999999" + "&period=" + "300"
        #
        #     print(url)
        #     api_response = requests.get(url).json()
        #
        #     closep = []
        #     for candle in api_response:
        #         price = float(candle["close"])
        #         closep.append(price)

        # weights = np.exp(np.linspace(-1., 0., period))
        # weights /= weights.sum()
        #
        # a = np.convolve(closep, weights, mode='full')[:len(closep)]
        # a[:period] = a[period]
        # return a

        # *** NEW ***
        ema = closep[0]
        emas = []
        multiplier = 2 / (period + 1)
        for i in range(0, len(closep)):
            ema = (float(closep[i]) - ema) * multiplier + ema
            emas.append(ema)
        return np.array(emas)


    def rsi(self, n=14, closep=None, ticker=None):
        # if closep is None:
        #     current_time = time.time()
        #     url = "https://poloniex.com/public?command=returnChartData&currencyPair=USDT_" + ticker + "&start=" + \
        #           str(current_time - 86000) + "&end=" + "9999999999" + "&period=" + "300"
        #
        #     print(url)
        #     api_response = requests.get(url).json()
        #
        #     closep = []
        #     for candle in api_response:
        #         price = float(candle["close"])
        #         closep.append(price)

        deltas = np.diff(closep)
        seed = deltas[:n + 1]
        up = seed[seed >= 0].sum() / n
        down = -seed[seed < 0].sum() / n
        # in case zero check
        rs = 0
        if down != 0:
            rs = up / down
        rsi = np.zeros_like(closep)
        rsi[:n] = 100. - 100. / (1. + rs)

        for i in range(n, len(closep)):
            delta = deltas[i - 1]  # cause the diff is 1 shorter

            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta

            up = (up * (n - 1) + upval) / n
            down = (down * (n - 1) + downval) / n

            if down != 0:
                rs = up / down
            else:
                rs = 0
            rsi[i] = 100. - 100. / (1. + rs)
        return rsi

    def macd(self, closep=None):
        # if not closep:
        #     current_time = time.time()
        #     url = "https://poloniex.com/public?command=returnChartData&currencyPair=USDT_" + ticker + "&start=" + \
        #           str(current_time - 86000) + "&end=" + "9999999999" + "&period=" + "300"
        #
        #     print(url)
        #     api_response = requests.get(url).json()
        #
        #     closep = []
        #     for candle in api_response:
        #         price = float(candle["close"])
        #         closep.append(price)

        ema_slow = self.ema(26, closep=closep)
        ema_fast = self.ema(12, closep=closep)
        macd_diff = ema_fast - ema_slow
        ema_of_macd = self.ema(9, closep=macd_diff)

        return macd_diff, macd_diff-ema_of_macd

    def monitor(self):

        current_time = time.time()
        text = ""

        for coin in self.coins:
            if coin.volume_median24h < 1:
                continue

            url = "https://poloniex.com/public?command=returnChartData&currencyPair=" + coin.market + '_' + coin.name + \
                  "&start=" + str(current_time - 180000) + "&end=" + "9999999999" + "&period=" + "900"
            try:
                api_response = requests.get(url).json()
            except Exception as e:
                text += "{}-{} API Unavailable".format(coin.market, coin.name)
                continue

            closep = []
            for candle in api_response:
                price = float(candle["close"])
                closep.append(price)

            prev_candle_volume = api_response[-2]["volume"]
            current_volume = api_response[-1]["volume"]

            prev_candle_price = api_response[-2]["close"]
            current_price = api_response[-1]["close"]

            #  *** RSI ***
            rsi_current = self.rsi(closep=closep)[-1]

            if rsi_current <= 30 and not coin.rsi_down:
                text += u"\U0001F4C9" + coin.market + " " + coin.name + " RSI < 30\n\n"
                coin.rsi_down = True
            else:
                if rsi_current > 30 and coin.rsi_down:
                    coin.rsi_down = False

            #  *** MACD ***

            ema_diff, macd_diff = self.macd(closep=closep)
            macd_prev2, macd_prev1, macd_current = macd_diff[-3:]
            ema_prev2, ema_prev1, ema_current = ema_diff[-3:]
            # print(coin.name, coin.market, macd_prev2, macd_prev1, macd_current)

            if macd_current <= 0 and coin.macd_increasing:
                coin.macd_increasing = False

            else:
                if not coin.macd_increasing and macd_current >= macd_prev1 >= macd_prev2 >= 0:
                    text += u"\U0001F319" + coin.market + " " + coin.name + " MACD Increasing\n\n"
                    coin.macd_increasing = True

            if ema_current <= 0 and coin.ema_increasing:
                coin.ema_increasing = False

            else:
                if not coin.ema_increasing and ema_prev2 > ema_prev1 > ema_current >= 0:
                    text += u"\U0001F319" + coin.market + " " + coin.name + " EMA Increasing\n\n"
                    coin.ema_increasing = True

            # *** VOLUME ***

            if current_volume > coin.volume_median24h*3 and current_volume > coin.prev_volume and \
               current_price > prev_candle_price and current_price > coin.prev_price and current_volume > prev_candle_volume:

                text += u"\U0001F4CA" + "{}-{} Volume of {} is {} times greater than 24h average\n\n"\
                                              .format(coin.market, coin.name,
                                                      format(current_volume, ".2f"),
                                                      format(current_volume/coin.volume_median24h, ".2f"))

            coin.prev_volume = current_volume
            coin.prev_price = current_price
        return text


if __name__ == "__main__":
    monitor = Monitor()
    text = monitor.monitor()
    print(text)
    # LOG = "/var/www/outputs/log.txt"
    # log_file = open(LOG, 'w+')
    # log_file.write("Opened process" + str(os.getpid()))
    # log_file.close()



