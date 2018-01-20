import csv
import requests

def main():
    # 2016 - 1451610966
    api_response = requests.get('https://poloniex.com/public?command=returnChartData&currencyPair=BTC_ETH&start=0000000000&end=9999999999&period=7200')
    json_api = api_response.json()

    with open("prices.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile, delimiter=' ',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
        for candle in json_api:
            price = float(candle["close"])
            writer.writerow([price])

if __name__ == '__main__':
    main()