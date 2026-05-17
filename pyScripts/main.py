from mcpi.minecraft import Minecraft
import time
import datetime
import gspread
import logging

google_sheet_id = str(input('Enter ID spreadsheet:\n'))
google_sheet_list_name = str(input('\nEnter list name\n'))
key_path = str(input('\nEnter Google Service Account key path:\n'))

CONFIG = {
    "mc_host": "localhost",
    "mc_port": 4711,
    "sheet_id": google_sheet_id, 
    "sheet_name": google_sheet_list_name,
    "poll_interval": 10,
    "known_players": []  
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler()]
)


class GIS_System:
    def __init__(self):
        self.mc = None
        self.ws = None
        self._connect_mc()
        self._connect_sheets()

    def _connect_mc(self):
        """Подключение к майнкрафту"""
        try:
            self.mc = Minecraft.create(CONFIG["mc_host"], CONFIG["mc_port"])
            # Тестовый запрос для проверки соединения
            self.mc.player.getPos()
            logging.info("майнкрафт подключен")
        except Exception as e:
            logging.error(f"Ошибка подключения к майнкрафту: {e}")
            self.mc = None

    def _connect_sheets(self):
        """Подключение к гугл таблицам"""
        try:
            self.gc = gspread.service_account(filename="KEY.json")
            self.sh = self.gc.open_by_key(CONFIG["sheet_id"])
            self.ws = self.sh.worksheet(CONFIG["sheet_name"])
            logging.info("Google Sheets подключен")
        except Exception as e:
            logging.error(f"Ошибка подключения к Google Sheets: {e}")
            self.ws = None

    def _get_player_ids(self):
        """Получение списка игроков"""
        if not self.mc:
            return []
        try:
            # Попытка получить все ID (требует RaspberryJuice 1.12.1+)
            ids = self.mc.getPlayerEntityIds()
            return [(pid, f"Player_{pid}") for pid in ids]
        except (AttributeError, ConnectionError):
            # Fallback: известные игроки из CONFIG
            result = []
            for name in CONFIG.get("known_players", []):
                try:
                    pid = self.mc.getPlayerEntityId(name)
                    result.append((pid, name))
                except:
                    pass
            return result

    def run(self):
        """Основной цикл логирования"""
        if not self.mc or not self.ws:
            logging.error("Нет активных подключений. Запуск невозможен.")
            return

        logging.info("Запись координат запущена...")
        
        # Создаём заголовок, если таблица пуста
        if self.ws.get("A1:E1") == [[""]]:
            self.ws.append_row(["Время", "Игрок", "X", "Y", "Z"])

        while True:
            try:
                rows = []
                players = self._get_player_ids()
                
                for pid, name in players:
                    pos = self.mc.entity.getPos(pid)
                    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    rows.append([
                        ts,
                        name,
                        round(pos.x, 2),
                        round(pos.y, 2),
                        round(pos.z, 2)
                    ])
                
                if rows:
                    self.ws.append_rows(rows, value_input_option="USER_ENTERED")
                    logging.info(f"Записано {len(rows)} строк")
                    
            except KeyboardInterrupt:
                logging.info("Остановка по Ctrl+C")
                break
            except Exception as e:
                logging.error(f"Ошибка в цикле: {e}")
                logging.warning("Переподключение...")
                self._connect_mc()
                self._connect_sheets()
            
            time.sleep(CONFIG["poll_interval"])


# ───────── ЗАПУСК ─────────
if __name__ == "__main__":
   
    app = GIS_System()  # Создаём экземпляр класса
    app.run()           # Запускаем метод у экземпляра