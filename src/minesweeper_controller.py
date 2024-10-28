import os
import time
from dataclasses import dataclass
from enum import Enum

from playwright.sync_api import sync_playwright, Page


@dataclass
class CellDataEnum(Enum):
    EMPTY = "cell size24 hd_opened hd_type0"
    N1 = "cell size24 hd_opened hd_type1"
    N2 = "cell size24 hd_opened hd_type2"
    N3 = "cell size24 hd_opened hd_type3"
    N4 = "cell size24 hd_opened hd_type4"
    N5 = "cell size24 hd_opened hd_type5"
    N6 = "cell size24 hd_opened hd_type6"
    N7 = "cell size24 hd_opened hd_type71"
    N8 = "cell size24 hd_opened hd_type8"
    FLAG_WITH_NO_MINE = "cell size24 hd_opened hd_type12"
    MINE = "cell size24 hd_opened hd_type11"
    CLOSED = "cell size24 hd_closed"
    FLAG = "cell size24 hd_closed hd_flag"
class MinesweeperBotWeb:
    _game_block_selector = "//div[@class='game-window-frame']"
    _face_selector = "//div[contains(@class,'smiley-container')]"
    _cell_selector = "//div[@id='cell_{x}_{y}']"

    def __init__(self):
        """
        :param url: URL страницы с веб-версией Сапера.
        """
        current_directory = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_directory, "winmine.html")
        self.url = f"file://{file_path}?height=8&width=8&mines=10"
        self.browser = None
        self.page:Page = None
        self.context = None

    def start_game(self):
        """Запуск браузера и загрузка страницы игры"""
        playwright = sync_playwright().start()
        self.browser = playwright.chromium.launch(headless=False)  # Отключаем headless для наблюдения
        self.context = self.browser.new_context()
        self.page:Page = self.context.new_page()
        self.page.goto(self.url)
        self.page.locator(self._face_selector).click()
        self.page.wait_for_timeout(1000)
    def restart_game(self):
        """Перезапуск игры (будет заполнено с селектором кнопки перезапуска)"""
        self.page.locator(self._face_selector).click()

    def left_click(self, x, y):
        """Левый клик по координате (x, y) (будет заполнено селекторами ячеек)"""
        # Здесь будет Playwright-селектор для ячейки на позиции (x, y)
        self.page.locator(self._cell_selector.format(x=x, y=y)).click()

    def right_click(self, x, y):
        """Правый клик по координате (x, y) (будет заполнено селекторами ячеек)"""
        # Здесь будет Playwright-селектор для ячейки на позиции (x, y)
        self.page.locator(self._cell_selector.format(x=x, y=y)).click(button="right")

    def get_game_state(self):
        """Проверка состояния игры (будет заполнено селекторами для отслеживания конца игры)"""
        if "game-over" in self.page.locator(self._face_selector).get_attribute("class"):
            return "lose"
        elif "win" in self.page.locator(self._face_selector).get_attribute("class"):
            return "win"
        else:
            return "inprogress"

    def get_cell_state(self, class_attr):
        if CellDataEnum.CLOSED.value == class_attr:
            return 99
        elif CellDataEnum.FLAG.value == class_attr:
            return -1
        elif CellDataEnum.MINE.value == class_attr:
            return -99
        elif CellDataEnum.FLAG_WITH_NO_MINE.value == class_attr:
            return -999
        elif CellDataEnum.EMPTY.value == class_attr:
            return 0
        elif CellDataEnum.N1.value == class_attr:
            return 1
        elif CellDataEnum.N2.value == class_attr:
            return 2
        elif CellDataEnum.N3.value == class_attr:
            return 3
        elif CellDataEnum.N4.value == class_attr:
            return 4
        elif CellDataEnum.N5.value == class_attr:
            return 5
        elif CellDataEnum.N6.value == class_attr:
            return 6
        elif CellDataEnum.N7.value == class_attr:
            return 7
        elif CellDataEnum.N8.value == class_attr:
            return 8

    def get_field_state(self):
        field_res = self.page.evaluate('''
            () => {
                const cells = document.querySelectorAll("[id^='cell_']");
                const field = [];

                // Маппинг классов клеток к их числовым состояниям
                const cellStateMap = {
                    "": 99,                     // CLOSED
                    "clear mine": -77,            // OTHER MINES
                    "clear triggered-mine mine": -77,           // EXPL MINE
                    "clear": 0,              // EMPTY
                    "clear c1": 1,              // N1
                    "clear c2": 2,              // N2
                    "clear c3": 3,              // N3
                    "clear c4": 4,              // N4
                    "clear c5": 5,              // N5
                    "clear c6": 6,              // N6
                    "clear c7": 7,             // N7
                    "clear c8": 8,               // N8
                };

                cells.forEach(cell => {
                    const id_attr = cell.id;
                    const class_attr = cell.className;
                    const col_index = parseInt(id_attr.split("_")[2]);
                    const row_index = parseInt(id_attr.split("_")[1]);

                    if (!field[row_index]) {
                        field[row_index] = [];
                    }

                    // Точное соответствие класса
                    const cell_state = cellStateMap[class_attr] !== undefined ? cellStateMap[class_attr] : null;

                    field[row_index][col_index] = cell_state;
                });

                return field;
            }
        ''')
        for y, row in enumerate(field_res):
            for x, value in enumerate(row):
                if value is None:
                    field_res[y][x] = -77
        return field_res

    def close_game(self):
        """Закрытие браузера"""
        if self.browser:
            self.browser.close()


