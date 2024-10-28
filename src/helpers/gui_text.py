import tkinter as tk
from PIL import Image, ImageDraw, ImageFont, ImageTk


class TransparentWindow:
    def __init__(self):
        # Создаём корень окна
        self.root = tk.Tk()
        self.root.overrideredirect(True)  # Убираем заголовок окна
        self.root.attributes('-transparentcolor', '#f0f0f0')  # Устанавливаем прозрачный цвет для фона

        # Устанавливаем окно на передний план (всегда поверх всех окон)
        self.root.attributes('-topmost', True)

        # Переменные для хранения изображения и метки
        self.label = None
        self.tk_image = None

        # Добавляем возможность перемещения окна
        self.root.bind('<Button-1>', self.click_window)
        self.root.bind('<B1-Motion>', self.drag_window)

    def create_transparent_text_image(self, text, size=30, text_color=(0, 0, 0, 255), image_size=(500, 200)):
        """
        Создаёт изображение с полупрозрачным текстом на полностью прозрачном фоне.
        :param text: Текст для отображения.
        :param size: Размер шрифта.
        :param text_color: Цвет текста (с альфа-каналом для прозрачности).
        :param image_size: Размер изображения (ширина, высота).
        :return: Изображение с текстом.
        """
        # Создание прозрачного изображения (фон полностью прозрачный)
        image = Image.new("RGBA", image_size, (255, 240, 240, 0))  # Прозрачный фон
        draw = ImageDraw.Draw(image)

        # Использование шрифта
        font = ImageFont.truetype("arial.ttf", size)  # Используй путь к шрифту, если требуется

        # Вычисление размеров текста
        bbox = draw.textbbox((0, 0), text, font=font)  # Получаем bounding box текста
        text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]

        # Центрирование текста
        position = ((image.width - text_width) // 2, (image.height - text_height) // 2)

        # Рисуем текст чёрным с полной непрозрачностью
        draw.text(position, text, font=font, fill=text_color)

        return image

    def update_text(self, text):
        """
        Обновляет текст в существующем окне.
        :param text: Новый текст для отображения.
        """
        # Создаём новое изображение с обновлённым текстом
        image = self.create_transparent_text_image(text, text_color=(0, 0, 0, 255))  # Чёрный цвет

        # Конвертируем изображение для использования в Tkinter
        self.tk_image = ImageTk.PhotoImage(image)

        # Если метка ещё не существует, создаём её
        if self.label is None:
            self.label = tk.Label(self.root, image=self.tk_image, bg='#f0f0f0')
            self.label.pack()
        else:
            # Обновляем изображение в существующей метке
            self.label.config(image=self.tk_image)
            self.label.image = self.tk_image  # Чтобы изображение не удалялось сборщиком мусора

    def click_window(self, event):
        """Сохраняем смещение курсора относительно окна при клике"""
        self._offset_x = event.x
        self._offset_y = event.y

    def drag_window(self, event):
        """Перемещаем окно по экрану"""
        x = event.x_root - self._offset_x
        y = event.y_root - self._offset_y
        self.root.geometry(f'+{x}+{y}')

    def start(self):
        """Запуск цикла Tkinter"""
        self.root.mainloop()


# Функция для обновления текста в фоновом процессе
def display_image_with_text(queue):
    window = TransparentWindow()  # Создаём объект окна

    # Проверяем очередь на наличие обновлений текста
    def check_queue():
        if not queue.empty():
            text = queue.get()  # Получаем текст из очереди
            window.update_text(text)  # Обновляем текст
        window.root.after(100, check_queue)  # Проверяем очередь каждые 100 мс

    check_queue()  # Начинаем проверку очереди
    window.start()  # Запуск Tkinter цикла
