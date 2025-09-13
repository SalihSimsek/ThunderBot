from flask import Flask
from threading import Thread
import logging

logging.getLogger('werkzeug').setLevel(logging.ERROR)  # logları temizler

app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    while True:  # hata olsa bile tekrar başlar
        try:
            app.run(host='0.0.0.0', port=8080)
        except:
            pass

def keep_alive():
    t = Thread(target=run)
    t.start()
