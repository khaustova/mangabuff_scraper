import nodriver as uc
from logger import setup_logger
from mangabuff_scraper import MangaBuffScraper

logger = setup_logger(__name__)


async def main():
    """
    Основная асинхронная функция для запуска скрипта фарма карточек.
    """

    # Получение пути к папке с профилем Chrome
    with open('user_data.txt', 'r', encoding='utf-8') as file:
        user_data_dir = file.read()

    # Инициализация браузера
    browser = await uc.start(
        headless=False,
        user_data_dir=user_data_dir,
    )

    # Создание экземпляра парсера
    mangabuff_scraper = MangaBuffScraper(browser)

    # Запуск функции чтения манги
    await mangabuff_scraper.start_reading_manga()


if __name__ == '__main__':
    # Запуск асинхронного цикла
    uc.loop().run_until_complete(main())
