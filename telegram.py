import requests
import os
import signal
from monitor import Monitor
import multiprocessing
import chart
import time
# import trades
import tradingview
from tinydb import TinyDB, Query
from creds import bot_token

ALERTS = "/var/www/outputs/alerts.txt"
BOT_URL = "https://api.telegram.org/bot{}/".format(bot_token)

db_state = multiprocessing.Value('i')


def handle_update(update):

    text = update["message"]["text"].lower()
    chat = update["message"]["chat"]["id"]
    try:
        request = text.split(" ")
        command = request[0]

        if command == "/users":
            db = TinyDB(os.path.join(os.path.dirname(__file__), 'db.json'))
            users = db.all()
            text = "USERS: "
            for user in users:
                text += str(user["id"]) + "\n"

        if command == "/chart":
            ticker = request[1].upper()
            try:
                chart.make_graph(ticker, 10, 30)
            except Exception as e:
                send_message("Error parsing data. Invalid ticker or API timeout\n"+str(e), chat)
                return

        # command for parsing tradingview website
        elif command == "/ideas":
            pages = int(request[1])
            hours = int(request[2])
            if pages > 20 or pages < 1:
                send_message("Max number of pages is 20", chat)
                return
            elif hours < 1:
                send_message("Please input positive number of hours", chat)
                return
            else:
                try:
                    text = "Parsing {} pages of tradingview.com in the last {} hours...".format(str(pages), str(hours))
                    send_message(text, chat)
                    text = tradingview.sort_and_order(tradingview.parse(pages, hours))
                except Exception as e:
                    send_message("Error parsing tradingview\n"+str(e), chat)

        # command for current bids/trades
        # elif command == "trades":
        #     text = trades.calculate(coins)

        elif command == "/help":
            text = "/ideas *pages* *hours* - parse ideas from #pages of tradingview.com in the last #hours\n" + \
                    "/monitor - begin monitoring crossovers of rsi, macd and volume above daily average\n" + \
                    "/stop - stop monitoring\n" + \
                    "/chart *ticker* - get a 24 hour graph of selected currency from poloniex\n"

        # command for setting up alarm notifications
        elif command == "/monitor":
            db = TinyDB(os.path.join(os.path.dirname(__file__), 'db.json'))
            User = Query()

            if db.search(User.id == chat):
                text = "Already subscribed"
                db.close()

            else:
                if not db.all():
                    db_state.value = 0
                    monitor_d = multiprocessing.Process(target=monitor_daemon, args=[db_state])
                    monitor_d.daemon = True
                    monitor_d.start()
                    text = "Monitoring process with PID {} is created".format(str(monitor_d.pid))

                    # write PID to textfile
                    try:
                        with open(ALERTS, 'w') as alerts:
                            alerts.write(str(monitor_d.pid))

                    except Exception as e:
                        text = "Failed to write pid to file"
                        send_message(str(e) + text, chat)
                        return

                db.insert({"id": chat})
                db.close()
                db_state.value = 1

        elif command == "/stop":
            db = TinyDB(os.path.join(os.path.dirname(__file__), 'db.json'))
            User = Query()
            db.remove(User.id == chat)
            db_state.value = 1

            try:
                if not db.all():
                    with open(ALERTS, 'r') as alerts:
                        pid = int(alerts.read())
                        os.kill(pid, signal.SIGKILL)
                    text = "Price monitoring stopped\n"
                db.close()
            except Exception as e:
                text = "Processes were not stopped\n" + str(e)

        elif command == "/purge":
            db = TinyDB(os.path.join(os.path.dirname(__file__), 'db.json'))
            db.purge()
            with open(ALERTS, 'r') as alerts:
                pid = int(alerts.read())
                os.kill(pid, signal.SIGKILL)
            text = "Price monitoring stopped for all users\n"
            db.close()

        if request[0] == "/chart":
            send_photo(chat)
        else:
            send_message(text, chat)

    except Exception as e:
        print(e)
        send_message(str(e) + "\n in handle_update", chat)


def monitor_daemon(db_update):
    interval = 120

    def update_users():
        database = TinyDB(os.path.join(os.path.dirname(__file__), 'db.json'))
        users_upd = database.all()
        database.close()
        print("updated users")
        return users_upd

    monitor = Monitor()

    db = TinyDB(os.path.join(os.path.dirname(__file__), 'db.json'))
    users = db.all()
    db.close()

    while True:
        try:
            if db_update.value:
                users = update_users()
                db_update.value = 0

            text = monitor.monitor()
            if text:
                for user in users:
                    send_message(text, user["id"])
            time.sleep(interval)

        except Exception as e:
            print("Exception in main loop " + str(e))
            return


def send_message(text, chat_id):
    url = BOT_URL+"sendMessage"
    data = {'chat_id': chat_id, 'text': text}
    request = requests.post(url, data=data)


def send_photo(chat_id):
    url = BOT_URL+"sendPhoto"
    files = {'photo': open(os.path.join(os.path.dirname(__file__), "example.png"), 'rb')}
    data = {'chat_id': chat_id}
    request = requests.post(url, data=data, files=files)


def main():
    pass

if __name__ == '__main__':
    main()
