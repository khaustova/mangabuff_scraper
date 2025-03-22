import logging
import sys


def setup_logger(name: str, log_file: str='app.log'):
    """
    Настройка и создание логгера.

    Args:
        name: Имя логгера (обычно используется __name__).
        log_file: Имя файла для записи логов. По умолчанию 'app.log'.

    Returns:
        logging.Logger: Настроенный логгер.
    """

    # Создание логгера
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG) # Установка уровня логирования  

    # Создание форматтер
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Создание обработчика для вывода в консоль
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Создание обработчика для записи в файл
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)

    # Добавление обработчиков к логгеру
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
