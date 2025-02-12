import os
import logging
from pypresence import Presence
from yaml import safe_load, YAMLError
from time import time, sleep
from os import system, name
import requests
import a2s
from functools import partial

VERSION = "0.3.0"
DEFAULT_CONFIG_FILE = "config.yml"
TRANSLATIONS_FILE = "translations.yml"

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

# - String -
# Language for RPC and messages (en/es/fr/etc)
lang: en
"""

DEFAULT_TRANSLATIONS = """translations:
  creating_config:
    en: "Creating default configuration file: {file}"
    es: "Creando archivo de configuración por defecto: {file}"
    fr: "Création du fichier de configuration par défaut : {file}"
    de: "Erstelle Standardkonfigurationsdatei: {file}"
    pt: "Criando arquivo de configuração padrão: {file}"
    ru: "Создание файла конфигурации по умолчанию: {file}"
    zh: "正在创建默认配置文件: {file}"
    ja: "デフォルト設定ファイルを作成中: {file}"
    ko: "기본 설정 파일 생성 중: {file}"
    it: "Creazione del file di configurazione predefinito: {file}"
    nl: "Standaard configuratiebestand aan het maken: {file}"
  config_not_found:
    en: "Configure {file} and restart the script."
    es: "Configura {file} y reinicia el script."
    fr: "Configurez {file} et redémarrez le script."
    de: "Konfiguriere {file} und starte das Skript neu."
    pt: "Configure {file} e reinicie o script."
    ru: "Настройте {file} и перезапустите скрипт."
    zh: "请配置 {file} 并重启脚本。"
    ja: "{file} を設定してスクリプトを再起動してください。"
    ko: "{file}을 구성하고 스크립트를 다시 시작하십시오."
    it: "Configura {file} e riavvia lo script."
    nl: "Configureer {file} en herstart het script."
  connected_api:
    en: "Connected to server via API: {ip_address}:{port}"
    es: "Conectado al servidor mediante API: {ip_address}:{port}"
    fr: "Connecté au serveur via l'API : {ip_address}:{port}"
    de: "Verbunden mit Server über API: {ip_address}:{port}"
    pt: "Conectado ao servidor via API: {ip_address}:{port}"
    ru: "Подключено к серверу через API: {ip_address}:{port}"
    zh: "已通过 API 连接到服务器: {ip_address}:{port}"
    ja: "API経由でサーバーに接続しました: {ip_address}:{port}"
    ko: "API를 통해 서버에 연결됨: {ip_address}:{port}"
    it: "Connesso al server tramite API: {ip_address}:{port}"
    nl: "Verbonden met server via API: {ip_address}:{port}"
  api_fallback:
    en: "Failed to fetch server info via API. Falling back to direct connection."
    es: "Error al obtener información del servidor mediante API. Volviendo a conexión directa."
    fr: "Échec de la récupération des informations du serveur via l'API. Retour à la connexion directe."
    de: "Fehler beim Abrufen der Serverinformationen über API. Fallback zur direkten Verbindung."
    pt: "Falha ao obter informações do servidor via API. Voltando para conexão direta."
    ru: "Не удалось получить информацию о сервере через API. Переключение на прямое подключение."
    zh: "通过 API 获取服务器信息失败。回退到直接连接。"
    ja: "API経由でサーバー情報を取得できませんでした。直接接続にフォールバックします。"
    ko: "API를 통해 서버 정보를 가져오지 못했습니다. 직접 연결로 대체합니다."
    it: "Impossibile recuperare le informazioni del server tramite API. Ritorno alla connessione diretta."
    nl: "Kon serverinfo niet ophalen via API. Terugvallen op directe verbinding."
  connected_direct:
    en: "Connected to server directly: {ip_address}:{port}"
    es: "Conectado al servidor directamente: {ip_address}:{port}"
    fr: "Connecté directement au serveur : {ip_address}:{port}"
    de: "Direkt mit Server verbunden: {ip_address}:{port}"
    pt: "Conectado ao servidor diretamente: {ip_address}:{port}"
    ru: "Подключено к серверу напрямую: {ip_address}:{port}"
    zh: "已直接连接到服务器: {ip_address}:{port}"
    ja: "サーバーに直接接続しました: {ip_address}:{port}"
    ko: "서버에 직접 연결됨: {ip_address}:{port}"
    it: "Connesso direttamente al server: {ip_address}:{port}"
    nl: "Direct verbonden met server: {ip_address}:{port}"
  connection_failed:
    en: "Failed to connect to server {ip}:{port}. Check the server status."
    es: "Error al conectar al servidor {ip}:{port}. Verifica el estado del servidor."
    fr: "Échec de la connexion au serveur {ip}:{port}. Vérifiez l'état du serveur."
    de: "Verbindung zu Server {ip}:{port} fehlgeschlagen. Überprüfe den Serverstatus."
    pt: "Falha ao conectar ao servidor {ip}:{port}. Verifique o status do servidor."
    ru: "Не удалось подключиться к серверу {ip}:{port}. Проверьте статус сервера."
    zh: "连接到服务器 {ip}:{port} 失败。请检查服务器状态。"
    ja: "サーバー {ip}:{port} への接続に失敗しました。サーバーのステータスを確認してください。"
    ko: "서버 {ip}:{port}에 연결하지 못했습니다. 서버 상태를 확인하십시오."
    it: "Impossibile connettersi al server {ip}:{port}. Controlla lo stato del server."
    nl: "Verbinding met server {ip}:{port} mislukt. Controleer de serverstatus."
  main_menu:
    en: "Main Menu"
    es: "Menú Principal"
    fr: "Menu Principal"
    de: "Hauptmenü"
    pt: "Menu Principal"
    ru: "Главное меню"
    zh: "主菜单"
    ja: "メインメニュー"
    ko: "메인 메뉴"
    it: "Menu principale"
    nl: "Hoofdmenu"
  playing_on:
    en: "Playing on {server_name} [{player_count}/{max_players}]"
    es: "Jugando en {server_name} [{player_count}/{max_players}]"
    fr: "Jouer sur {server_name} [{player_count}/{max_players}]"
    de: "Spielt auf {server_name} [{player_count}/{max_players}]"
    pt: "Jogando em {server_name} [{player_count}/{max_players}]"
    ru: "Играет на {server_name} [{player_count}/{max_players}]"
    zh: "正在 {server_name} 上玩 [{player_count}/{max_players}]"
    ja: "{server_name} でプレイ中 [{player_count}/{max_players}]"
    ko: "{server_name}에서 플레이 중 [{player_count}/{max_players}]"
    it: "Giocando su {server_name} [{player_count}/{max_players}]"
    nl: "Speelt op {server_name} [{player_count}/{max_players}]"
  map:
    en: "Map: {map_name}"
    es: "Mapa: {map_name}"
    fr: "Carte: {map_name}"
    de: "Karte: {map_name}"
    pt: "Mapa: {map_name}"
    ru: "Карта: {map_name}"
    zh: "地图: {map_name}"
    ja: "マップ: {map_name}"
    ko: "맵: {map_name}"
    it: "Mappa: {map_name}"
    nl: "Kaart: {map_name}"
  status_main_menu:
    en: "Currently in Main Menu. No server connection."
    es: "Actualmente en el Menú Principal. Sin conexión al servidor."
    fr: "Actuellement dans le Menu Principal. Pas de connexion au serveur."
    de: "Aktuell im Hauptmenü. Keine Serververbindung."
    pt: "Atualmente no Menu Principal. Sem conexão com o servidor."
    ru: "В данный момент в главном меню. Нет подключения к серверу."
    zh: "当前在主菜单中。未连接到服务器。"
    ja: "現在メインメニューにいます。サーバーに接続されていません。"
    ko: "현재 메인 메뉴에 있습니다. 서버에 연결되지 않았습니다."
    it: "Attualmente nel Menu principale. Nessuna connessione al server."
    nl: "Momenteel in het hoofdmenu. Geen serververbinding."
  status_updated:
    en: "Updated RPC: Playing on {server_name} (Map: {map_name}, Players: {player_count}/{max_players})"
    es: "RPC actualizado: Jugando en {server_name} (Mapa: {map_name}, Jugadores: {player_count}/{max_players})"
    fr: "RPC mis à jour : Jouer sur {server_name} (Carte: {map_name}, Joueurs: {player_count}/{max_players})"
    de: "RPC aktualisiert: Spielt auf {server_name} (Karte: {map_name}, Spieler: {player_count}/{max_players})"
    pt: "RPC atualizado: Jogando em {server_name} (Mapa: {map_name}, Jogadores: {player_count}/{max_players})"
    ru: "RPC обновлен: Играет на {server_name} (Карта: {map_name}, Игроки: {player_count}/{max_players})"
    zh: "RPC已更新: 正在 {server_name} 上玩 (地图: {map_name}, 玩家: {player_count}/{max_players})"
    ja: "RPCを更新しました: {server_name} でプレイ中 (マップ: {map_name}, プレイヤー: {player_count}/{max_players})"
    ko: "RPC 업데이트됨: {server_name}에서 플레이 중 (맵: {map_name}, 플레이어: {player_count}/{max_players})"
    it: "RPC aggiornato: Giocando su {server_name} (Mappa: {map_name}, Giocatori: {player_count}/{max_players})"
    nl: "RPC bijgewerkt: Speelt op {server_name} (Kaart: {map_name}, Spelers: {player_count}/{max_players})"
  rpc_connected:
    en: "Discord RPC connected successfully."
    es: "Conexión a Discord RPC exitosa."
    fr: "Connexion à Discord RPC réussie."
    de: "Discord RPC erfolgreich verbunden."
    pt: "RPC Discord conectado com sucesso."
    ru: "Discord RPC подключен успешно."
    zh: "Discord RPC 连接成功。"
    ja: "Discord RPCが正常に接続されました。"
    ko: "Discord RPC가 성공적으로 연결되었습니다."
    it: "Discord RPC connesso con successo."
    nl: "Discord RPC succesvol verbonden."
  config_reloaded:
    en: "Config file reloaded with new settings."
    es: "Archivo de configuración recargado con nuevas opciones."
    fr: "Fichier de configuration rechargé avec les nouveaux paramètres."
    de: "Konfigurationsdatei mit neuen Einstellungen neu geladen."
    pt: "Arquivo de configuração recarregado com novas configurações."
    ru: "Файл конфигурации перезагружен с новыми настройками."
    zh: "配置文件已重新加载并应用新设置。"
    ja: "設定ファイルが新しい設定で再読み込みされました。"
    ko: "설정 파일을 새 설정으로 다시 로드했습니다."
    it: "File di configurazione ricaricato con nuove impostazioni."
    nl: "Configuratiebestand herladen met nieuwe instellingen."
  missing_api_keys:
    en: "Missing required API keys: {missing}. Please update the config."
    es: "Faltan claves de API requeridas: {missing}. Actualiza la configuración."
    fr: "Clés API manquantes : {missing}. Veuillez mettre à jour la configuration."
    de: "Fehlende erforderliche API-Schlüssel: {missing}. Bitte aktualisiere die Konfiguration."
    pt: "Chaves de API obrigatórias ausentes: {missing}. Por favor, atualize a configuração."
    ru: "Отсутствуют необходимые ключи API: {missing}. Пожалуйста, обновите конфигурацию."
    zh: "缺少必需的 API 密钥: {missing}。请更新配置。"
    ja: "必要なAPIキーがありません: {missing}。設定を更新してください。"
    ko: "필수 API 키가 누락되었습니다: {missing}. 구성을 업데이트하십시오."
    it: "Chiavi API richieste mancanti: {missing}. Aggiorna la configurazione."
    nl: "Vereiste API-sleutels ontbreken: {missing}. Werk de configuratie bij."
  error_config:
    en: "Error loading config file: {error}"
    es: "Error al cargar el archivo de configuración: {error}"
    fr: "Erreur lors du chargement du fichier de configuration : {error}"
    de: "Fehler beim Laden der Konfigurationsdatei: {error}"
    pt: "Erro ao carregar o arquivo de configuração: {error}"
    ru: "Ошибка загрузки файла конфигурации: {error}"
    zh: "加载配置文件时出错: {error}"
    ja: "設定ファイルの読み込みエラー: {error}"
    ko: "설정 파일 로드 오류: {error}"
    it: "Errore durante il caricamento del file di configurazione: {error}"
    nl: "Fout bij het laden van configuratiebestand: {error}"
  error_rpc_setup:
    en: "Failed to set up Discord RPC: {error}"
    es: "Error al configurar Discord RPC: {error}"
    fr: "Échec de la configuration de Discord RPC : {error}"
    de: "Fehler beim Einrichten von Discord RPC: {error}"
    pt: "Falha ao configurar o Discord RPC: {error}"
    ru: "Не удалось настроить Discord RPC: {error}"
    zh: "设置 Discord RPC 失败: {error}"
    ja: "Discord RPCの設定に失敗しました: {error}"
    ko: "Discord RPC 설정 실패: {error}"
    it: "Impossibile configurare Discord RPC: {error}"
    nl: "Discord RPC instellen mislukt: {error}"
  rpc_closed:
    en: "Discord RPC connection closed."
    es: "Conexión a Discord RPC cerrada."
    fr: "Connexion à Discord RPC fermée."
    de: "Discord RPC-Verbindung geschlossen."
    pt: "Conexão RPC Discord fechada."
    ru: "Соединение Discord RPC закрыто."
    zh: "Discord RPC 连接已关闭。"
    ja: "Discord RPC接続が閉じられました。"
    ko: "Discord RPC 연결이 닫혔습니다."
    it: "Connessione Discord RPC chiusa."
    nl: "Discord RPC-verbinding gesloten."
  translations_reloaded:
    en: "Translations file reloaded."
    es: "Archivo de traducciones recargado."
    fr: "Fichier de traductions rechargé."
    de: "Übersetzungsdatei neu geladen."
    pt: "Arquivo de traduções recarregado."
    ru: "Файл переводов перезагружен."
    zh: "翻译文件已重新加载。"
    ja: "翻訳ファイルが再読み込みされました。"
    ko: "번역 파일이 다시 로드되었습니다."
    it: "File delle traduzioni ricaricato."
    nl: "Vertalingenbestand herladen."
  error_translations_reload:
    en: "Error reloading translations: {error}"
    es: "Error al recargar las traducciones: {error}"
    fr: "Erreur lors du rechargement des traductions : {error}"
    de: "Fehler beim Neuladen der Übersetzungen: {error}"
    pt: "Erro ao recarregar as traduções: {error}"
    ru: "Ошибка перезагрузки переводов: {error}"
    zh: "重新加载翻译时出错: {error}"
    ja: "翻訳の再読み込みエラー: {error}"
    ko: "번역 다시 로드 오류: {error}"
    it: "Errore durante il ricaricamento delle traduzioni: {error}"
    nl: "Fout bij het herladen van vertalingen: {error}"
  error_general:
    en: "An unexpected error occurred: {error}"
    es: "Ocurrió un error inesperado: {error}"
    fr: "Une erreur inattendue est survenue : {error}"
    de: "Ein unerwarteter Fehler ist aufgetreten: {error}"
    pt: "Ocorreu um erro inesperado: {error}"
    ru: "Произошла неожиданная ошибка: {error}"
    zh: "发生意外错误: {error}"
    ja: "予期しないエラーが発生しました: {error}"
    ko: "예기치 않은 오류가 발생했습니다: {error}"
    it: "Si è verificato un errore inatteso: {error}"
    nl: "Er is een onverwachte fout opgetreden: {error}"
"""

logging.basicConfig(
    filename="cs16_rpc.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class Translator:
    def __init__(self, translations_data, lang='en'):
        self.translations = translations_data
        self.lang = lang

    def get(self, key, default=None, **kwargs):
        msg = self.translations.get(key, {}).get(self.lang, None)
        if msg is None:
            msg = self.translations.get(key, {}).get('en', default)
        if msg is None:
            return f"Missing translation: {key}"
        try:
            return msg.format(**kwargs)
        except KeyError as e:
            logging.error(f"Missing placeholder {e} in translation key {key}")
            return msg

def clear_screen():
    system("cls" if name == "nt" else "clear")

def check_config():
    if not os.path.exists(DEFAULT_CONFIG_FILE):
        print(f"Creating default configuration file: {DEFAULT_CONFIG_FILE}")
        with open(DEFAULT_CONFIG_FILE, "w") as f:
            f.write(DEFAULT_CONFIG)
        return False
    return True

def get_server_info(config, translator):
    if config.get("use_api"):
        try:
            api_url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={config['api_key']}&steamids={config['steamid']}"
            resp = requests.get(api_url, timeout=5).json()
            gameserverip = resp["response"]["players"][0]["gameserverip"].split(":")
            ip_address = gameserverip[0]
            port = int(gameserverip[1])
            server = a2s.info((ip_address, port), timeout=5.0)
            print(translator.get('connected_api', ip_address=ip_address, port=port))
            return server, f"{ip_address}:{port}"
        except Exception as e:
            logging.error(f"API Error: {e}")
            print(translator.get('api_fallback'))
            return None, None
    else:
        try:
            ip_address = config["ip"]
            port = int(config["port"])
            server = a2s.info((ip_address, port), timeout=5.0)
            print(translator.get('connected_direct', ip_address=ip_address, port=port))
            return server, f"{ip_address}:{port}"
        except Exception as e:
            logging.error(f"Connection Error: {e}")
            print(translator.get('connection_failed', ip=config['ip'], port=config['port']))
            return None, None

def update_rpc(rpc, server_info, ipserver, start_time, translator):
    if server_info is None:
        state = translator.get('main_menu')
        details = ""
        large_image = "1"
        large_text = "Counter-Strike"
        rpc.update(
            state=state,
            details=details,
            large_image=large_image,
            large_text=large_text
        )
        return translator.get('status_main_menu')
    else:
        state = translator.get('playing_on',
                                            server_name=server_info.server_name,
                                            player_count=server_info.player_count,
                                            max_players=server_info.max_players)
        details = translator.get('map', map_name=server_info.map_name)
        large_image = "1"
        large_text = "Counter-Strike"
        rpc.update(
            state=state,
            details=details,
            large_image=large_image,
            large_text=large_text,
            start=start_time
        )
        return translator.get('status_updated',
                                            server_name=server_info.server_name,
                                            map_name=server_info.map_name,
                                            player_count=server_info.player_count,
                                            max_players=server_info.max_players)

def main():
    if not check_config():
        print(f"Configure {DEFAULT_CONFIG_FILE} and restart the script.")
        return

    if not os.path.exists(TRANSLATIONS_FILE):
        try:
            with open(TRANSLATIONS_FILE, 'w', encoding='utf-8') as f:
                f.write(DEFAULT_TRANSLATIONS)
            print(f"Created default translations file: {TRANSLATIONS_FILE}")
        except Exception as e:
            logging.error(f"Failed to create translations file: {e}")
            print(f"Error creating translations file: {e}")
            return

    try:
        with open(DEFAULT_CONFIG_FILE, "r") as f:
            config = safe_load(f)
    except (YAMLError, IOError) as e:
        logging.error(f"Config Error: {e}")
        print(f"Error loading config file: {e}")
        return

    try:
        with open(TRANSLATIONS_FILE, 'r', encoding='utf-8') as f:
            loaded_data = safe_load(f)
            if loaded_data is None:
                translations_data = {}
            else:
                translations_data = loaded_data.get('translations', {})
    except Exception as e:
        logging.error(f"Failed to load translations: {e}")
        translations_data = {}
        print(f"Error loading translations: {e}")

    translator = Translator(translations_data, config.get('lang', 'en'))
    last_modified = os.path.getmtime(DEFAULT_CONFIG_FILE)
    last_translations_modified = os.path.getmtime(TRANSLATIONS_FILE)

    try:
        rpc = Presence("763064337031888946")
        rpc.connect()
        start_time = time()
        print(translator.get('rpc_connected'))
        try:
            while True:
                sleep(5)
                clear_screen()
                print(translator.get('rpc_connected') + "\n")

                current_modified = os.path.getmtime(DEFAULT_CONFIG_FILE)
                current_translations_modified = os.path.getmtime(TRANSLATIONS_FILE)

                if current_modified > last_modified:
                    with open(DEFAULT_CONFIG_FILE, "r") as f:
                        new_config = safe_load(f)
                    config = new_config
                    last_modified = current_modified
                    translator = Translator(translations_data, config.get('lang', 'en'))
                    print(translator.get('config_reloaded') + "\n")

                if current_translations_modified > last_translations_modified:
                    try:
                        with open(TRANSLATIONS_FILE, 'r', encoding='utf-8') as f:
                            new_translations = safe_load(f).get('translations', {})
                        translations_data = new_translations
                        translator = Translator(translations_data, config.get('lang', 'en'))
                        last_translations_modified = current_translations_modified
                        print(translator.get('translations_reloaded') + "\n")
                    except Exception as e:
                        logging.error(f"Error reloading translations: {e}")
                        print(translator.get('error_translations_reload', error=e) + "\n")

                if config.get("use_api"):
                    missing = [k for k in ("api_key", "steamid") if k not in config]
                    if missing:
                        logging.error(f"Missing API keys: {missing}")
                        print(translator.get('missing_api_keys', missing=', '.join(missing)) + "\n")
                        continue

                server_info, ipserver = get_server_info(config, translator)
                status_message = update_rpc(rpc, server_info, ipserver, start_time, translator)
                print(status_message)

        except Exception as e:
            logging.exception("Main loop error:")
            print(translator.get('error_general', error=e))
            sleep(10)
        finally:
            rpc.close()
            print(translator.get('rpc_closed'))
    except Exception as e:
        logging.exception("RPC setup failed:")
        print(translator.get('error_rpc_setup', error=e))

if __name__ == "__main__":
    main()
