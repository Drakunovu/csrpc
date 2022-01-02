from pypresence import Presence
from yaml import safe_load
from time import time, sleep
from os import path, system, name
import requests
import a2s

version = "0.1.0"


def check_config():
    if path.exists("config.yml"):
        print(
            "Counter-Strike 1.6 RPC has been created by Drakunovu#9424\n" + version + "\n\nConfiguration file has been found, using it...\n"
        )
    else:
        open("config.yml", "w").write(default_config)


def get_info():
    main_menu = -1
    if bool(config["use_api"]) == True:
        try:
            resp = requests.get(api_url).json()
            gameserverip = resp["response"]["players"][0]["gameserverip"].split(":")
            ipserver = resp["response"]["players"][0]["gameserverip"]
            server = a2s.info((str(gameserverip[0]), int(gameserverip[1])))
        except:
            main_menu = True
    else:
        try:
            server = a2s.info((str(config["ip"]), int(config["port"])))
            ipserver = str(config["ip"]) + ":" + str(config["port"])
        except:
            main_menu = True

    if main_menu == True:
        return "main_menu"
    else:
        return server


clear = lambda: system("cls" if name == "nt" else "clear")

iTimer = time()

RPC = Presence("763064337031888946")
RPC.connect()

default_config = """# - Boolean -
# Can be useful if you wanna see what kind of info you are pulling off
debug: false

# - String -
# IP Address of the server
ip: 127.0.0.1

# - Integer -
# Port of the server
port: 27015

# - Boolean -
# If true, it will be using the 2 values below, and it will update the IP and Port of the server whatever you go automatically.
# Also this will display Main Menu automatically if you are in the menu.
use_api: false

# - String -
# The Steam Web API Key, this can be obtained in https://steamcommunity.com/devapikey
api_key: W129IFHNQWOH12T128912

# - Integer -
# Your SteamID64, this can be obtained using a tool like https://steamid.io or https://www.steamidfinder.com/ and pasting your Profile URL
steamid: 123712651272152171
"""

check_config()
config = safe_load(open("config.yml", "r", errors="ignore"))
ipserver = -1
api_url = (
    "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key="
    + str(config["api_key"])
    + "&steamids="
    + str(config["steamid"])
)

while True:
    sleep(5)
    clear()

    if bool(config["use_api"]) == False:
        config = safe_load(open("config.yml", "r", errors="ignore"))

    infoServer = get_info()
    player_count = infoServer.player_count + 1
    print("Updating with the last information available")

    if infoServer == "main_menu":
        RPC.update(
            **{"state": "Main Menu", "large_image": "1", "large_text": "Counter-Strike"}
        )
    else:
        RPC.update(
            **{
                "state": "Playing on "
                + infoServer.server_name
                + " ["
                + str(player_count)
                + "/"
                + str(infoServer.max_players)
                + "]",
                "details": "Map: " + infoServer.map_name,
                "large_image": "1",
                "large_text": "Counter-Strike",
                "start": iTimer,
                "buttons": [
                    {
                        "label": "Join",
                        "url": "steam://connect/" + str(ipserver),
                    }
                ],
            }
        )
