import logging
import time
import multiprocessing
import gymnasium as gym
import numpy as np
from gymnasium import spaces

from src.helpers.gui_text import display_image_with_text
from src.minesweeper_controller import MinesweeperBotWeb

logging.basicConfig(
    level=logging.WARN,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("../main.log"),  # Логирование в файл
        logging.StreamHandler()  # Логирование в консоль
    ]
)

logger = logging.getLogger(__name__)


class MinesweeperEnv(gym.Env):
    def __init__(self):
        super(MinesweeperEnv, self).__init__()
        self.frame_height = 8
        self.frame_width = 8
        self.minesweeper_bot = MinesweeperBotWeb()
        self.action_space = spaces.MultiDiscrete([1, self.frame_height, self.frame_width])
        self.observation_space = self._initialize_observation_space()
        self.game_state = "inprogress"
        self.wins = 0
        self.loses = 0
        self.max_reward = 0
        self.reward = 0
        self.steps_counter = 0
        self.field_state = None

        # Создаём очередь для передачи данных в фоновый процесс
        self.queue = multiprocessing.Queue()

        # Запуск процесса отображения окна с текстом
        self.image_process = multiprocessing.Process(target=display_image_with_text, args=(self.queue,))
        self.image_process.start()

        # Запускаем игру
        self.minesweeper_bot.start_game()

    def _initialize_observation_space(self):
        return spaces.Dict({
            'field_state': spaces.Box(low=0, high=255, shape=(self.frame_height, self.frame_width), dtype=np.int32),
            'game_state': spaces.Discrete(3)
        })

    def reset(self, seed=None, options=None, attempt=0):
        logger.info("Executing reset")
        super().reset(seed=seed)
        self.steps_counter = 0
        self.minesweeper_bot.restart_game()
        self.field_state = None
        observation, info = self._get_observation()
        logger.info("Finishing reset")
        return observation, info

    def step(self, action):
        logger.info("Executing step")
        action_type, x, y = action
        # Выполняем действие: левый клик или правый клик (пометить мину)
        if self.field_state[x][y] != 99:
            reward = -10
            observation, info = self._get_observation()
            terminated = self._check_done()
            truncated = False
            return observation, reward, terminated, truncated, info
        self.minesweeper_bot.left_click(x, y)
        self.steps_counter += 1
        observation, info = self._get_observation()
        reward = self._calculate_reward()
        terminated = self._check_done()
        truncated = False

        return observation, reward, terminated, truncated, info

    def _get_observation(self):
        logger.info("Get observation")
        self.game_state = self.minesweeper_bot.get_game_state()
        self.field_state = self.minesweeper_bot.get_field_state()
        int_game_state = 0
        if self.game_state == "win":
            int_game_state = 1
        elif self.game_state == "lose":
            int_game_state = 2
        elif self.game_state == "inprogress":
            int_game_state = 0
        return {
            'field_state': self.field_state,
            'game_state': int_game_state
        }, {}

    def _calculate_reward(self):
        logger.info("Calculate reward")

        reward = 0

        if self.game_state == "win":
            reward += 1000
        elif self.game_state == "lose":
            reward -= 500

        reward += self.steps_counter * 10

        logger.info(f"Total reward: {reward}")
        self.queue.put(f"Wins: {self.wins} | Loses: {self.loses}\n"
                       f"Last reward: {reward}\n"
                       f"Max reward: {self.max_reward}")
        self.max_reward = reward if reward > self.max_reward else self.max_reward
        return reward

    def _check_done(self):
        logger.info("check_done")
        self.game_state = self.minesweeper_bot.get_game_state()

        if self.game_state in ["win", "lose"]:
            # Обновляем счётчики побед и поражений
            if self.game_state == "win":
                self.wins += 1
            if self.game_state == "lose":
                self.loses += 1
            return True
        return False

    def close(self):
        """
        Завершение процесса с текстом при завершении работы окружения.
        """
        if self.image_process.is_alive():
            self.image_process.terminate()
            self.image_process.join()
        super().close()
