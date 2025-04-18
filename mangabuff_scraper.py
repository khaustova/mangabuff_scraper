import asyncio
import random
import time
from logger import setup_logger
from nodriver.core.browser import Browser
from nodriver.core.tab import Tab

logger = setup_logger(__name__)


class MangaBuffScraper:
    """
    Класс для фарма карточек на сайте mangabuff.ru.

    Attributes:
        browser: Браузер для открытия страниц.
        notifications_page: Страница уведомлений для отслеживания уведомлений
            о новых карточках.
    """
    def __init__(self, browser: Browser):
        self.browser = browser
        self.notifications_page = None

    async def start_reading_manga(self) -> None:
        """
        Метод для запуска чтения манги из файла manga.txt.
        """
        # Открытие страницы уведомлений
        self.notifications_page = await self.browser.get(
            'https://mangabuff.ru/notifications'
        )

        # Получение списка ссылок на мангу из файла
        with open('manga.txt', 'r+', encoding='utf-8') as file_with_manga:
            manga_list = file_with_manga.read().splitlines()

        # Чтение каждой манги из списка
        for manga_num, manga_link in enumerate(manga_list):
            logger.info('Начато чтение манги %s', manga_link)
            await self._read_manga(manga_num, manga_link)

    async def _read_manga(self, manga_num: int, manga_link: str) -> None:
        """
        Метод для чтения манги по ссылке. 

        Args:
            manga_num: Номер со строкой ссылки на мангу в файле manga.txt
            manga_link: Ссылка на мангу.
        """
        manga_page = await self.browser.get(f'{manga_link}', new_tab=True)
        await manga_page.get_content()
        time.sleep(random.randint(3, 5))

        # Извлечение номера главы и названия манги из ссылки
        chapter = int(manga_link.split('/')[-1])
        manga_name = manga_link.split('/')[-3]

        # Получение списка полученных карт
        current_cards = await self.notifications_page.find_all(
            'Вы получили новую карту'
        )
        while True:
            #await self._read_chapter(manga_page)
            await self._scroll_chapter(manga_page)

            # Обновление ссылки на главу в файле manga.txt
            new_manga_link = await manga_page.evaluate('window.location.href')
            await self._update_manga_link_in_file(manga_num, new_manga_link)

            # Проверка новых уведомлений
            await self.notifications_page.reload()
            await self.notifications_page.get_content()
            check_current_cards = await self.notifications_page.find_all(
                'Вы получили новую карту'
            )

            # Переход к следующей главе
            try:
                next_button = await manga_page.find('След. глава')
                chapter += 1
                is_more_chapters = True

                await next_button.click()
                time.sleep(random.randint(3, 5))
                
                await manga_page.reload()
                time.sleep(random.randint(3, 5))
                
                logger.debug('Переходим к главе %s манги %s', chapter, manga_name)
            except Exception:
                await self._delete_read_manga_link_in_file(manga_num)
                is_more_chapters = False
                
                logger.info('Главы закончились')

            # Если получена новая карта, ждем около часа
            if len(current_cards) < len(check_current_cards):
                logger.debug(
                    'Была получена новая карта! Переходим в режим ожидания...'
                )
                new_manga_link = await manga_page.evaluate('window.location.href')
                await manga_page.close()
                time.sleep(random.randint(3605, 3615))

                if not is_more_chapters:
                    return None

                current_cards = check_current_cards
                manga_page = await self.browser.get(new_manga_link, new_tab=True)

            time.sleep(random.randint(1, 3))

    async def _scroll_chapter(self, manga_page: Tab) -> None:
        """
        Метод для прокрутки страницы с главой манги.

        Args:
            manga_page: Отрытая в браузере страница с мангой.
        """
        last_height = await manga_page.evaluate('document.documentElement.scrollHeight')
        step = 1
        while True:
            # Плавная прокрутка вниз
            await manga_page.evaluate('window.scrollBy(0, 300)')
            await asyncio.sleep(0.2)

            # Плавная прокрутка вверх
            if step % 50 == 0:
                for _ in range(5):
                    await manga_page.evaluate('window.scrollBy(0, -300)')
                    await asyncio.sleep(0.2)
                await asyncio.sleep(0.8)

            # Получаение новых данных о высоте страницы
            new_height = await manga_page.evaluate('document.documentElement.scrollHeight')
            current_position = await manga_page.evaluate('window.pageYOffset + window.innerHeight')

            # Проверка достижение конца страницы
            if abs(new_height - current_position) < 100:
                break

            last_height = max(last_height, new_height)
            step += 1

    async def _update_manga_link_in_file(
        self,
        manga_num: int,
        new_manga_link: str
    ) -> None:
        """
        Метод обновления ссылки на мангу после прочтения главы для учитывания
        прогресса чтения.
        
        Args:
            manga_num: Индекс строки с читаемой мангой в файле.
            new_manga_link: Новая ссылка на читаемую мангу.
        
        """
        new_manga_link = new_manga_link[:-1] + str(int(new_manga_link[-1]) + 1)

        with open('manga.txt', 'r', encoding='utf-8') as file_with_manga:
            lines = file_with_manga.readlines()

        lines[manga_num] = new_manga_link + '\n'

        with open('manga.txt', 'w', encoding='utf-8') as file_with_manga:
            file_with_manga.writelines(lines)

    async def _delete_read_manga_link_in_file(
        self,
        manga_num: int,
    ) -> None:
        """
        Метод удаления ссылки на прочитанную мангу.
        
        Args:
            manga_num: Индекс строки с читаемой мангой в файле.
        
        """
        with open('manga.txt', 'r', encoding='utf-8') as file_with_manga:
            lines = file_with_manga.readlines()

        lines = lines[manga_num + 1:]

        with open('manga.txt', 'w', encoding='utf-8') as file_with_manga:
            file_with_manga.writelines(lines)

    async def get_manga_links(
        self,
        base_url: str='https://mangabuff.ru/manga',
        pages: int=36,

    ) -> list[str]:
        """
        Метод парсинга ссылок на мангу.
        
        Args:
            base_url: Ссылка на страницу для парсинга. 
                По умолчанию 'https://mangabuff.ru/manga'.
            pages: Количество страниц, которые нужно спарсить. По умолчанию 36.

        Returns:
            list: Список ссылок на мангу.
        """
        manga_links = []

        # Проход по страницам сайта
        for i in range(1, pages + 1):
            page = await self.browser.get(base_url + str(i))
            time.sleep(random.randint(3, 5))
            await page.get_content()
            links_list = await page.get_all_urls()

            # Фильтрация ссылок
            for link in links_list:
                if (link.startswith('https://mangabuff.ru/manga/')
                    and link != 'https://mangabuff.ru/manga/top'
                    and link not in manga_links
                ):
                    manga_links.append(link)

        return manga_links
