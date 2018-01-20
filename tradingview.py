from bs4 import BeautifulSoup
import json
from pandas.io.json import json_normalize
import requests
from datetime import datetime, timedelta


def get_html(url):
    r = requests.get(url)
    return r.text


def get_ideas(html, hours):
    soup = BeautifulSoup(html, 'lxml')
    content = soup.find(True, {"class" : ["div.tv-feed", "js-balancer"]})
    ideas = content.find_all("div", {"data-widget-type": "idea"})

    result = []

    for idea in ideas:
        time_info = idea.find("span", {"class": "tv-widget-idea__time"})
        timestamp = time_info["data-timestamp"]
        current_time = datetime.utcnow()
        idea_datetime = datetime.utcfromtimestamp(float(timestamp))

        if idea_datetime < current_time - timedelta(hours=hours):
            continue

        pro_status = idea.find("a", {"class": "tv-user-badge"})
        if pro_status:
            pro_status = pro_status.get_text()
        else:
            continue

        human_time = idea_datetime.strftime('%d-%m-T%H:%M:%SZ')

        signal_span = idea.find("span", {"class": "tv-idea-label"})
        # print(signal_span + "\n")
        signal = "None"
        if signal_span:
            signal = signal_span.get_text()

        data_json = idea['data-widget-data']
        data = json.loads(data_json)
        data.update({"Timestamp": timestamp})
        data.update({"Signal": signal})
        data.update({"When": human_time})
        result.append(data)

    return result


def parse(num_pages, hours):
    base = "https://www.tradingview.com/markets/cryptocurrencies/"
    page = "/page-"

    all_ideas = []
    for i in range(1, num_pages+1):
        url = base + page + str(i) + '/'
        page_html = get_html(url)
        all_ideas += get_ideas(page_html, hours)

    print(all_ideas)
    ticker_list = {}

    for idea in all_ideas:
        if idea["short_symbol"] not in ticker_list and idea["Signal"] != "None":
            ticker_list.update({idea["short_symbol"]: {"shorts": 0, "longs": 0}})
        if idea["Signal"] == "Short":
            ticker_list[idea["short_symbol"]]["shorts"] += 1
        elif idea["Signal"] == "Long":
            ticker_list[idea["short_symbol"]]["longs"] += 1

    print(ticker_list)
    return ticker_list
    # return json.dumps(ticker_list)


def csv_export(all_ideas):   
    df = json_normalize(all_ideas)
    df_sorted = df.sort_values(by='Timestamp', ascending=False)
    df_sorted.to_csv("ideas.csv")


def sort_and_order(result):
    order = sorted(result.items(), key=lambda x: x[1]["longs"], reverse=True)
    result = ""
    for idea in order:
        result += "{} - Longs: {}, Shorts: {}\n".format(idea[0], idea[1]["longs"], idea[1]["shorts"])
    # print(result+"\n")
    return result

def main():
    result = parse(10, 24)
    print(sort_and_order(result))
    # print(sort_and_order(result))

if __name__ == "__main__":
    main()
