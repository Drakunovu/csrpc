import os
import logging
from pypresence import Presence
from yaml import safe_load, YAMLError
from time import time, sleep
from os import system, name
import requests
import a2s

# Constants
VERSION = "0.2.0"  # Script version
DEFAULT_CONFIG_FILE = "config.yml"  # Default configuration file name

# Default configuration template
DEFAULT_CONFIG = """# - Boolean -
# Can be useful if you wanna see what kind of info you are pulling off
debug: false

# - String -
# IP Address of the server
ip: 127.0.0.1

# - Integer -
# Port of the server
port: 27015

# - Boolean -
# If true, it will use the API to fetch server info dynamically.
# Displays Main Menu if not in a server.
use_api: false

# - String -
# Steam Web API Key from https://steamcommunity.com/dev/apikey
api_key: YOUR_API_KEY

# - Integer -
# Your SteamID64 (find via https://steamid.io)
steamid: YOUR_STEAMID
"""

# Configure logging to write errors to a log file
logging.basicConfig(
    filename="cs16_rpc.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def clear_screen():
    """
    Clears the console screen.
    Uses 'cls' for Windows and 'clear' for Unix-based systems.
    """
    system("cls" if name == "nt" else "clear")

def check_config():
    """
    Checks if the configuration file exists. If not, creates a default one.
    Returns True if the config file exists, False if it was created.
    """
    if not os.path.exists(DEFAULT_CONFIG_FILE):
        print(f"Creating default configuration file: {DEFAULT_CONFIG_FILE}")
        with open(DEFAULT_CONFIG_FILE, "w") as f:
            f.write(DEFAULT_CONFIG)
        return False
    return True

def get_server_info(config):
    """
    Fetches server information either via the Steam API or directly.
    Returns a tuple containing the server info and the server address (IP:Port).
    If an error occurs, returns (None, None).
    """
    if config.get("use_api"):
        try:
            # Fetch current server info via Steam API
            api_url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={config['api_key']}&steamids={config['steamid']}"
            resp = requests.get(api_url, timeout=5).json()
            gameserverip = resp["response"]["players"][0]["gameserverip"].split(":")
            ip_address = gameserverip[0]
            port = int(gameserverip[1])
            server = a2s.info((ip_address, port), timeout=5.0)
            print(f"Connected to server via API: {ip_address}:{port}")
            return server, f"{ip_address}:{port}"
        except Exception as e:
            logging.error(f"API Error: {e}")
            print("Failed to fetch server info via API. Falling back to direct connection.")
            return None, None
    else:
        try:
            # Fetch server info directly using the IP and port from the config
            ip_address = config["ip"]
            port = int(config["port"])
            server = a2s.info((ip_address, port), timeout=5.0)
            print(f"Connected to server directly: {ip_address}:{port}")
            return server, f"{ip_address}:{port}"
        except Exception as e:
            logging.error(f"Connection Error: {e}")
            print(f"Failed to connect to server {config['ip']}:{config['port']}. Check the server status.")
            return None, None

def update_rpc(rpc, server_info, ipserver, start_time):
    """
    Updates the Discord Rich Presence status based on the server info.
    Returns a status message describing the current RPC state.
    """
    if server_info is None:
        # If no server info is available, set RPC to "Main Menu"
        rpc.update(
            state="Main Menu",
            large_image="1",
            large_text="Counter-Strike"
        )
        return "Currently in Main Menu. No server connection."
    else:
        # Update RPC with server details
        rpc.update(
            state=f"Playing on {server_info.server_name} [{server_info.player_count}/{server_info.max_players}]",
            details=f"Map: {server_info.map_name}",
            large_image="1",
            large_text="Counter-Strike",
            start=start_time
        )
        return f"Updated RPC: Playing on {server_info.server_name} (Map: {server_info.map_name}, Players: {server_info.player_count}/{server_info.max_players})"

def main():
    """
    Main function to handle the script's logic.
    """
    # Check if the config file exists, create it if it doesn't
    if not check_config():
        print(f"Configure {DEFAULT_CONFIG_FILE} and restart the script.")
        return

    try:
        # Load the configuration file
        with open(DEFAULT_CONFIG_FILE, "r") as f:
            config = safe_load(f)
    except (YAMLError, IOError) as e:
        logging.error(f"Config Error: {e}")
        print(f"Error loading config file: {e}")
        return

    # Track the last modified time of the config file
    last_modified = os.path.getmtime(DEFAULT_CONFIG_FILE)

    try:
        # Initialize Discord RPC
        rpc = Presence("763064337031888946")
        rpc.connect()
        start_time = time()
        print("Discord RPC connected successfully.")
        try:
            while True:
                sleep(5)  # Wait 5 seconds between updates
                clear_screen()  # Clear the console before printing new information

                # Re-display the permanent message
                print("Discord RPC connected successfully.\n")

                # Check if the config file has been modified
                current_modified = os.path.getmtime(DEFAULT_CONFIG_FILE)
                if current_modified > last_modified:
                    # Reload the config file if it has been modified
                    with open(DEFAULT_CONFIG_FILE, "r") as f:
                        new_config = safe_load(f)
                    config = new_config
                    last_modified = current_modified
                    logging.info("Config reloaded")
                    print("Config file reloaded with new settings.\n")

                # Validate API config if use_api is enabled
                if config.get("use_api"):
                    missing = [k for k in ("api_key", "steamid") if k not in config]
                    if missing:
                        logging.error(f"Missing API keys: {missing}")
                        print(f"Missing required API keys: {missing}. Please update the config.\n")
                        continue

                # Fetch server info and update RPC
                server_info, ipserver = get_server_info(config)
                status_message = update_rpc(rpc, server_info, ipserver, start_time)
                print(status_message)  # Print the latest status

        except Exception as e:
            # Handle errors in the main loop
            logging.exception("Main loop error:")
            print(f"Error in main loop: {e}")
            sleep(10)  # Prevent tight loop on errors
        finally:
            # Clean up RPC connection
            rpc.close()
            print("Discord RPC connection closed.")
    except Exception as e:
        # Handle errors during RPC setup
        logging.exception("RPC setup failed:")
        print(f"Failed to set up Discord RPC: {e}")

if __name__ == "__main__":
    main()