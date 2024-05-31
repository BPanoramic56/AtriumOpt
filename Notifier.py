import configparser
import http.client, urllib

config = configparser.ConfigParser()
config.read("configurations.ini")

Token = config["Notifier Information"]["Token"]
User = config["Notifier Information"]["User"]

def notify(title, message, url, priority):
    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
    urllib.parse.urlencode({
        "token": Token,
        "user": User,
        "title": title,
        "message": message,
        "url": url,
        "priority": priority
    }), { "Content-type": "application/x-www-form-urlencoded" })
    conn.getresponse()