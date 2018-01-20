import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt

import os
import time
import numpy as np
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
from matplotlib.finance import candlestick_ohlc
import matplotlib
import pylab
import requests

matplotlib.rcParams.update({'font.size': 9})


def rsiFunc(prices, n=14):
    deltas = np.diff(prices)
    seed = deltas[:n + 1]
    up = seed[seed >= 0].sum() / n
    down = -seed[seed < 0].sum() / n
    rs = up / down
    rsi = np.zeros_like(prices)
    rsi[:n] = 100. - 100. / (1. + rs)

    for i in range(n, len(prices)):
        delta = deltas[i - 1]  # cause the diff is 1 shorter

        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta

        up = (up * (n - 1) + upval) / n
        down = (down * (n - 1) + downval) / n

        rs = up / down
        rsi[i] = 100. - 100. / (1. + rs)

    return rsi


def movingaverage(values, window):
    weigths = np.repeat(1.0, window) / window
    smas = np.convolve(values, weigths, 'valid')
    return smas  # as a numpy array


def ExpMovingAverage(values, window):
    weights = np.exp(np.linspace(-1., 0., window))
    weights /= weights.sum()
    a = np.convolve(values, weights, mode='full')[:len(values)]
    a[:window] = a[window]
    return a


def computeMACD(x, slow=26, fast=12):
    emaslow = ExpMovingAverage(x, slow)
    emafast = ExpMovingAverage(x, fast)
    return emaslow, emafast, emafast - emaslow


def make_graph(ticker, ma1, ma2):
    pair = "BTC_" + ticker
    if ticker == "BTC":
        pair = "USDT_BTC"

    current_time = time.time()
    url = "https://poloniex.com/public?command=returnChartData&currencyPair=" + pair + "&start=" + \
          str(current_time - 113400) + "&end=" + "9999999999" + "&period=" + "900"

    api_response = requests.get(url).json()

    stock_data = []
    for candle in api_response:
        line = str(candle["date"]) + " " + str(candle["high"]) + " " + str(candle["low"]) + " " + str(
            candle["open"]) + " " + str(candle["close"]) + " " + str(candle["volume"]) + '\n'
        stock_data.append(line)

    date, highp, lowp, openp, closep, volume = np.loadtxt(stock_data,
                                                          delimiter=' ',
                                                          unpack=True)

    dateconv = np.vectorize(mdates.epoch2num)
    date = dateconv(date)

    x = 0
    y = len(date)
    newAr = []
    while x < y:
        appendLine = date[x], openp[x], highp[x], lowp[x], closep[x], volume[x]
        newAr.append(appendLine)
        x += 1

    Av1 = movingaverage(closep, ma1)
    Av2 = movingaverage(closep, ma2)

    SP = len(date[ma2 - 1:])

    fig = plt.figure(facecolor='#07000d')

    ax1 = plt.subplot2grid((6, 4), (1, 0), rowspan=4, colspan=4, facecolor='#07000d')
    candlestick_ohlc(ax1, newAr[-SP:], width=.0025, colorup='#53c156', colordown='#ff1717')

    Label1 = str(ma1) + ' SMA'
    Label2 = str(ma2) + ' SMA'

    ax1.plot(date[-SP:], Av1[-SP:], '#e1edf9', label=Label1, linewidth=1.5)
    ax1.plot(date[-SP:], Av2[-SP:], '#4ee6fd', label=Label2, linewidth=1.5)

    ax1.grid(True, color='w')
    # ax1.xaxis.set_major_locator(mticker.MaxNLocator(10))
    ax1.xaxis.set_major_locator(mdates.HourLocator(byhour=range(0,25,2), interval=1))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

    ax1.yaxis.label.set_color("w")
    ax1.spines['bottom'].set_color("#5998ff")
    ax1.spines['top'].set_color("#5998ff")
    ax1.spines['left'].set_color("#5998ff")
    ax1.spines['right'].set_color("#5998ff")
    ax1.tick_params(axis='y', colors='w')
    plt.gca().yaxis.set_major_locator(mticker.MaxNLocator(prune='upper'))
    ax1.tick_params(axis='x', colors='w')
    plt.ylabel('Stock price and Volume')

    maLeg = plt.legend(loc=9, ncol=2, prop={'size': 7},
                       fancybox=True, borderaxespad=0.)
    maLeg.get_frame().set_alpha(0.4)
    textEd = pylab.gca().get_legend().get_texts()
    pylab.setp(textEd[0:5], color='w')

    volumeMin = 0

    ax0 = plt.subplot2grid((6, 4), (0, 0), sharex=ax1, rowspan=1, colspan=4, facecolor='#07000d')
    rsi = rsiFunc(closep)
    rsiCol = '#c1f9f7'
    posCol = '#386d13'
    negCol = '#8f2020'

    ax0.plot(date[-SP:], rsi[-SP:], rsiCol, linewidth=1.5)
    ax0.axhline(70, color=negCol)
    ax0.axhline(30, color=posCol)
    ax0.fill_between(date[-SP:], rsi[-SP:], 70, where=(rsi[-SP:] >= 70), facecolor=negCol, edgecolor=negCol,
                     alpha=0.5)
    ax0.fill_between(date[-SP:], rsi[-SP:], 30, where=(rsi[-SP:] <= 30), facecolor=posCol, edgecolor=posCol,
                     alpha=0.5)
    ax0.set_yticks([30, 70])
    ax0.yaxis.label.set_color("w")
    ax0.spines['bottom'].set_color("#5998ff")
    ax0.spines['top'].set_color("#5998ff")
    ax0.spines['left'].set_color("#5998ff")
    ax0.spines['right'].set_color("#5998ff")
    ax0.tick_params(axis='y', colors='w')
    ax0.tick_params(axis='x', colors='w')
    plt.ylabel('RSI')

    ax1v = ax1.twinx()
    volumeAverage = np.average(volume)
    ax1v.fill_between(date[-SP:], volume[-SP:], volumeAverage, where=(volume[-SP:] >= volumeAverage), facecolor='#f4f442', alpha=.3)
    ax1v.fill_between(date[-SP:], volumeMin, volume[-SP:], facecolor='#00ffe8', alpha=.2)
    ax1v.axes.yaxis.set_ticklabels([])
    ax1v.grid(False)
    ###Edit this to 3, so it's a bit larger
    ax1v.set_ylim(0, 3 * volume.max())
    ax1v.spines['bottom'].set_color("#5998ff")
    ax1v.spines['top'].set_color("#5998ff")
    ax1v.spines['left'].set_color("#5998ff")
    ax1v.spines['right'].set_color("#5998ff")
    ax1v.tick_params(axis='x', colors='w')
    ax1v.tick_params(axis='y', colors='w')
    ax2 = plt.subplot2grid((6, 4), (5, 0), sharex=ax1, rowspan=1, colspan=4, facecolor='#07000d')
    fillcolor = '#00ffe8'
    nslow = 26
    nfast = 12
    nema = 9
    emaslow, emafast, macd = computeMACD(closep)
    ema9 = ExpMovingAverage(macd, nema)
    ax2.plot(date[-SP:], macd[-SP:], color='#4ee6fd', lw=2)
    ax2.plot(date[-SP:], ema9[-SP:], color='#e1edf9', lw=1)

    ax2.fill_between(date[-SP:], macd[-SP:] - ema9[-SP:], 0, alpha=0.2, facecolor=fillcolor, edgecolor=fillcolor)

    ax2.axhline(0, color='b', alpha=0.2)
    ax2.fill_between(date[-SP:], macd[-SP:] - ema9[-SP:], 0, where=(macd[-SP:] >= ema9[-SP:]), alpha=0.5, facecolor=posCol, edgecolor=fillcolor)
    ax2.fill_between(date[-SP:], macd[-SP:] - ema9[-SP:], 0, where=(macd[-SP:] < ema9[-SP:]), alpha=0.5, facecolor=negCol, edgecolor=fillcolor)

    plt.gca().yaxis.set_major_locator(mticker.MaxNLocator(prune='upper'))
    ax2.spines['bottom'].set_color("#5998ff")
    ax2.spines['top'].set_color("#5998ff")
    ax2.spines['left'].set_color("#5998ff")
    ax2.spines['right'].set_color("#5998ff")
    ax2.tick_params(axis='x', colors='w')
    ax2.tick_params(axis='y', colors='w')
    plt.ylabel('MACD', color='w')
    ax2.yaxis.set_major_locator(mticker.MaxNLocator(nbins=5, prune='upper'))
    for label in ax2.xaxis.get_ticklabels():
        label.set_rotation(45)

    plt.suptitle(pair.upper(), color='w')
    plt.setp(ax0.get_xticklabels(), visible=False)
    plt.setp(ax1.get_xticklabels(), visible=False)

    plt.subplots_adjust(left=.09, bottom=.14, right=.94, top=.95, wspace=.20, hspace=0)
    # plt.show()
    fig.savefig(os.path.join(os.path.dirname(__file__), "example.png"), facecolor=fig.get_facecolor())


def main():
    make_graph("BTC", 10, 30)
    print("Chart saved")

if __name__ == "__main__":
    main()
