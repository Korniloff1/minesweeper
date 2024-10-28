import os
import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("main.log"),  # Логирование в файл
        logging.StreamHandler()  # Логирование в консоль
    ]
)

logger = logging.getLogger(__name__)
def add_string_to_file(file_path, string_to_add):
    if not os.path.exists(file_path):
        with open(file_path, 'w'):
            pass
    with open(file_path, 'a') as file:
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        file.write(f"{current_time}:{string_to_add}\n")