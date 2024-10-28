import logging
import os
import json
import argparse
from stable_baselines3 import PPO, DQN
from stable_baselines3.common.callbacks import CheckpointCallback, BaseCallback

from constants import PPO_CHECKPOINT_DIR, DQN_CHECKPOINT_DIR
from src.learning.ppo_env.sweeper_env_ppo import MinesweeperEnv


class SaveProgressCallback(BaseCallback):
    n_calls: int = 0

    def __init__(self, save_path, save_freq=100000, verbose=0):
        super(SaveProgressCallback, self).__init__(verbose)
        self.save_path = save_path
        self.save_freq = save_freq

    def _on_step(self) -> bool:
        if self.n_calls % self.save_freq == 0:
            if os.path.exists(self.save_path):
                with open(self.save_path, "r") as f:
                    data = json.load(f)
                current_timesteps = data.get("timesteps", 0)
            else:
                current_timesteps = 0
            current_timesteps += self.save_freq
            with open(self.save_path, "w") as f:
                json.dump({"timesteps": current_timesteps}, f)

        return True


def setup_logging():
    logging.basicConfig(
        level=logging.WARN,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler("main.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def load_progress(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
        return data.get("timesteps", 0)
    return 0


def find_latest_checkpoint(checkpoint_dir, model_type):
    checkpoint_files = [f for f in os.listdir(checkpoint_dir) if f.startswith(f'{model_type.lower()}_model') and f.endswith('.zip')]
    if checkpoint_files:
        checkpoint_files.sort(key=lambda x: os.path.getmtime(os.path.join(checkpoint_dir, x)), reverse=True)
        return os.path.join(checkpoint_dir, checkpoint_files[0])
    return None


def main(model_type):
    logger = setup_logging()

    # Определяем пути и классы в зависимости от типа модели
    if model_type == "PPO":
        env_class = MinesweeperEnv
        model_class = PPO
        checkpoint_dir = PPO_CHECKPOINT_DIR
    else:
        logger.error(f"Unsupported model type: {model_type}")
        return

    os.makedirs(checkpoint_dir, exist_ok=True)

    checkpoint_callback = CheckpointCallback(
        save_freq=100000,
        save_path=checkpoint_dir,
        name_prefix=f'{model_type.lower()}_model',
        save_replay_buffer=True
    )

    progress_file = os.path.join(checkpoint_dir, "progress.json")
    progress_callback = SaveProgressCallback(save_path=progress_file, save_freq=100000)

    latest_checkpoint = find_latest_checkpoint(checkpoint_dir, model_type)
    starting_timesteps = load_progress(progress_file)

    env = env_class()
    if latest_checkpoint:
        logger.warning(f"Found latest checkpoint: {latest_checkpoint}")
        try:
            model = model_class.load(latest_checkpoint)
            logger.warning("Checkpoint loaded successfully.")
            logger.warning(f"Restored progress: {starting_timesteps} timesteps")
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            logger.warning("Starting training from scratch.")
            if model_type == "DQN":
                model = model_class("MultiInputPolicy", env, buffer_size=10000, verbose=1)  # Уменьшенный buffer_size
            else:
                model = model_class("MultiInputPolicy", env, verbose=1)
    else:
        logger.warning("No checkpoint found. Creating a new model.")
        if model_type == "DQN":
            model = model_class("MultiInputPolicy", env, buffer_size=10000, verbose=1)  # Уменьшенный buffer_size
        else:
            model = model_class("MultiInputPolicy", env, verbose=1)

    # Убедитесь, что модель использует правильное окружение
    if not model.get_env():
        model.set_env(env)

    # Чтение общего количества таймстепов и установка новой цели
    total_timesteps = 10000000
    while True:
        model.learn(total_timesteps=total_timesteps, callback=[checkpoint_callback, progress_callback],
                    reset_num_timesteps=False)
        model.save(f"{os.path.join(checkpoint_dir, model_type.lower())}_drone_model_{load_progress(progress_file)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Choose the model type for training (PPO or DQN).")
    parser.add_argument('--model_type', type=str, choices=['PPO', 'DQN'], required=True, help="The model type to use for training (PPO or DQN).", default="PPO")
    args = parser.parse_args()
    main(args.model_type)
