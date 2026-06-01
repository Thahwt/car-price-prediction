import os
import re
import sys
import json
import time
import argparse
import requests
from tqdm import tqdm
from header import HEADERS
from bs4 import BeautifulSoup
from selenium.webdriver import Edge

from crawler import Crawler
from base import BaseClass
from common import is_file_empty


# ============================================================
# CONSTANTS & PATHS
# ============================================================
DATA_DIR = 'data/bonbanh'
BRANDS_LINK_FILE = f'{DATA_DIR}/brands_urls.txt'
CARS_LINK_FILE = f'{DATA_DIR}/cars_urls.txt'
CARS_DATA_FILE = f'{DATA_DIR}/used_cars.json'
FAILED_ITEMS_FILE = f'{DATA_DIR}/failed_items.json'
BASE_URL = 'https://bonbanh.com/'


# ============================================================
# SCRAPER
# ============================================================
class BonBanhScraper(BaseClass):
    def __init__(self, url, session=None):
        super().__init__()
        self.url = url
        self.session = session or Edge(options=HEADERS)
        self.log.info('Connecting to %s' % self.url)
        self.session.get(url)
        time.sleep(1)
        self.soup = BeautifulSoup(self.session.page_source, 'html.parser')

    # ── Helpers ──────────────────────────────────────────────

    def _car_name_normalizer(self, brand, model, name):
        name = name.lower().replace(brand.lower(), '').replace(model.lower(), '')
        return " ".join(name.split()[1:-1]) or None

    def _get_date(self, date_str):
        date = re.search(r'\d{1,2}/\d{1,2}/\d{4}', date_str)
        return date.group() if date else date_str

    def _extract_price(self, car_title):
        price_part = car_title.split('-')[-1].strip()
        normalized = price_part.lower().strip().split()
        price_pairs = [(int(normalized[i - 1]), normalized[i]) for i in range(1, len(normalized), 2)]

        total = 0
        for value, unit in price_pairs:
            if unit == 'triệu':
                total += value * 1_000_000
            elif unit in ('tỷ', 'tỉ'):
                total += value * 1_000_000_000
            else:
                return None
        return total

    def _extract_origin(self, text):
        t = text.lower()
        if 'nhập khẩu' in t:
            return 'imported'
        elif 'trong nước' in t:
            return 'domestic'
        return text

    def _extract_status(self, text):
        t = text.lower()
        if 'xe đã dùng' in t:
            return 'used'
        elif 'mới' in t:
            return 'new'
        return text

    def _extract_transmission(self, text):
        t = text.lower()
        if 'số tự động' in t:
            return 'automatic'
        elif 'số sàn' in t:
            return 'manual'
        return text

    def _extract_fuel(self, fuel_str):
        fuel_str = fuel_str.lower().replace('l', '')
        fuel_map = {'xăng': 'gasoline', 'dầu': 'diesel', 'điện': 'electric', 'hybrid': 'hybrid'}
        
        if fuel_str == 'điện':
            return fuel_map.get(fuel_str, "electric"), None
        
        fuel, volume = fuel_str.split()
        fuel_map = {'xăng': 'gasoline', 'dầu': 'diesel', 'điện': 'electric', 'hybrid': 'hybrid'}
        return fuel_map.get(fuel, fuel), float(volume)

    def _extract_color(self, color):
        if not color:
            return 'other'
        color_map = {
            'đen': 'black', 'trắng': 'white', 'kem': 'cream', 'đỏ': 'red',
            'xanh': 'blue', 'vàng': 'yellow', 'cam': 'orange', 'hồng': 'pink',
            'tím': 'purple', 'nâu': 'brown', 'xám': 'gray', 'ghi': 'silver_gray',
            'bạc': 'silver', 'cát': 'beige', 'đồng': 'copper', 'nhiều màu': 'multicolor'
        }
        return color_map.get(color.strip().lower(), 'other')

    def _extract_seats(self, text):
        match = re.search(r'\d+', text)
        return int(match.group()) if match else None

    def _extract_doors(self, text):
        match = re.search(r'\d+', text)
        return int(match.group()) if match else None

    def _extract_odo(self, text):
        match = re.search(r'[\d,.]+', text)
        if match:
            return int(match.group().replace(',', '').replace('.', ''))
        return None

    def _extract_drive(self, text):
        return text.lower().strip().split()[0]

    def _extract_location(self):
        contact_container = self.soup.select('div.contact-txt')
        if contact_container:
            for text_line in contact_container[0].stripped_strings:
                if 'Địa chỉ' in text_line:
                    return text_line.replace('Địa chỉ:','').strip()
        return 'Unknown'

    # ── Extractors ───────────────────────────────────────────

    def _extract_header_info(self):
        model_tags = self.soup.select('div.breadcrum span [itemprop="name"]')
        name_tags = self.soup.select('div.breadcrum span b')
        date_tags = self.soup.select('div.notes')
        title_tags = self.soup.select('div.title h1')

        brand = model_tags[2].text.strip()
        model = model_tags[3].text.strip()
        name = self._car_name_normalizer(brand, model, name_tags[0].text.strip())
        price = self._extract_price(title_tags[0].text.strip())
        date = self._get_date(date_tags[0].text.strip())

        return name.lower(), brand.lower(), model.lower(), date, price

    def _extract_detail_info(self):
        info_tags = self.soup.select('div#car_detail div.txt_input span')
        seat_door_tags = self.soup.select('div#mail_parent div.inputbox span')

        status = self._extract_status(info_tags[1].text.strip())
        fuel, volume = self._extract_fuel(info_tags[6 if status == 'used' else 5].text.strip())

        if status == 'used':
            return {
                'year': int(info_tags[0].text.strip()),
                'status': status,
                'odo': self._extract_odo(info_tags[2].text.strip()),
                'origin': self._extract_origin(info_tags[3].text.strip()),
                'style': info_tags[4].text.strip().lower(),
                'transmission': self._extract_transmission(info_tags[5].text.strip()),
                'engine': fuel,
                'volume': volume,
                'exterior_color': self._extract_color(info_tags[7].text.strip()),
                'interior_color': self._extract_color(info_tags[8].text.strip()),
                'seats': self._extract_seats(seat_door_tags[0].text.strip()),
                'doors': self._extract_doors(seat_door_tags[1].text.strip()),
                'drive': self._extract_drive(info_tags[9].text.strip()),
            }
        else:
            return {
                'year': int(info_tags[0].text.strip()),
                'status': status,
                'origin': self._extract_origin(info_tags[2].text.strip()),
                'style': info_tags[3].text.strip().lower(),
                'transmission': self._extract_transmission(info_tags[4].text.strip()),
                'engine': fuel,
                'volume': volume,
                'exterior_color': self._extract_color(info_tags[6].text.strip()),
                'interior_color': self._extract_color(info_tags[7].text.strip()),
                'seats': self._extract_seats(seat_door_tags[0].text.strip()),
                'doors': self._extract_doors(seat_door_tags[1].text.strip()),
                'drive': self._extract_drive(info_tags[8].text.strip()),
            }

    def extract(self):
        trim, brand, model, date, price = self._extract_header_info()
        detail_info = self._extract_detail_info()
        location = self._extract_location()
        return {
            'url': self.url,
            'brand': brand,
            'model': model,
            'trim': trim,
            'date': date,
            'price': price,
            'location': location,
            **detail_info
        }


# ============================================================
# CRAWLER
# ============================================================
class BonBanhCrawler(Crawler):
    def __init__(self):
        super().__init__()
        self.log.info('Connecting to %s' % BASE_URL)
        self.session = Edge()
        self.session.get(BASE_URL)
        self.soup = BeautifulSoup(self.session.page_source, 'html.parser')
        os.makedirs(DATA_DIR, exist_ok=True)

    # ── Internal helpers ──────────────────────────────────────

    def _load_existing_urls(self):
        """Load tất cả URL đã có trong file data để kiểm tra trùng."""
        if not os.path.exists(CARS_DATA_FILE) or is_file_empty(CARS_DATA_FILE):
            return set()
        with open(CARS_DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                return {item['url'] for item in data if 'url' in item}
            except json.JSONDecodeError:
                return set()

    def _load_existing_crawled_links(self):
        """Load các URL xe đã crawl từ file links."""
        if not os.path.exists(CARS_LINK_FILE) or is_file_empty(CARS_LINK_FILE):
            return []
        with open(CARS_LINK_FILE, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]

    # ── Step 1: Crawl brand links ─────────────────────────────

    def _get_brand_links(self):
        self.log.info('Extracting brand links from website')
        selector = '#primary-nav'
        brands = []

        transparent = self.soup.select(selector)[0].find_all(
            'li', attrs={'class': 'menuparent', 'style': 'z-index:999;'}
        )
        hidden = self.soup.select(selector)[0].find_all(
            'li', attrs={'class': 'menuparent add_menu'}
        )

        for item in transparent:
            brands.append(BASE_URL + item.find('a')['href'])
        for item in hidden:
            brands.append(BASE_URL + item.find('span')['url'])

        with open(BRANDS_LINK_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(brands))

        self.log.info('Found %d brand links' % len(brands))
        return brands

    # ── Step 2: Crawl car links ───────────────────────────────

    def crawl_links(self):
        """
        Thu thập URL xe từ tất cả các trang.
        Dừng sớm khi gặp URL đã tồn tại trong data (vì data được sắp xếp theo thời gian).
        Ghi thêm (append) các URL mới vào file links.
        """
        self.log.info('=== CRAWL LINKS MODE ===')

        existing_data_urls = self._load_existing_urls()
        existing_link_urls = set(self._load_existing_crawled_links())

        self.log.info('Existing data URLs: %d' % len(existing_data_urls))

        brand_links = self._get_brand_links()
        new_links = []
        stop_signal = False

        for brand_link in brand_links:       
            if stop_signal:
                break

            self.log.info("Crawling brand: %s" % brand_link)
            time.sleep(1)
            self.session.get(brand_link)
            soup = BeautifulSoup(self.session.page_source, 'html.parser')

            # Lấy số trang
            try:
                last_page_container = soup.select(
                    '#s-list-car > div > div.pagging > div.navpage > div'
                )[0].find_all('span')
                clean_link = brand_link.split('\n')[0]
                last_page = int(last_page_container[-1]['url'][len(clean_link + '/page,'):])
                pages = [clean_link + '/page,' + str(i) for i in range(1, last_page + 1)]
            except (KeyError, IndexError):
                pages = [brand_link]

            for page_url in pages:
                if stop_signal:
                    break

                self.log.info("Crawling page: %s" % page_url)
                time.sleep(1)

                try:
                    req = requests.get(page_url, headers=HEADERS).text
                    page_soup = BeautifulSoup(req, 'html.parser')
                    table = page_soup.select('#s-list-car > div > ul')[0]
                    li_tags = table.find_all('li', attrs={'itemtype': 'http://schema.org/Car'})
                except Exception as e:
                    self.log.error('Error fetching page %s: %s' % (page_url, str(e)))
                    continue

                for li in li_tags:
                    car_url = BASE_URL + li.find('a')['href']

                    # Gặp URL đã có trong data → dữ liệu cũ bắt đầu, dừng crawl
                    if car_url in existing_data_urls:
                        self.log.info('Found existing URL, stopping early: %s' % car_url)
                        stop_signal = True
                        break

                    # Chưa có trong links file → thêm mới
                    if car_url not in existing_link_urls:
                        new_links.append(car_url)
                        existing_link_urls.add(car_url)
                
                # Lưu tạm sau mỗi trang để tránh mất dữ liệu nếu bị lỗi giữa chừng
                if new_links:
                     with open(CARS_LINK_FILE, 'a', encoding='utf-8') as f:
                        f.write('\n'.join(new_links) + '\n')
                     self.log.info('Added %d new links so far...' % len(new_links))
                     new_links = []

        # Ghi thêm URL mới vào đầu file (mới nhất trước)
        if new_links:
            old_links = self._load_existing_crawled_links()
            all_links = new_links + old_links       # mới nhất ở đầu
            with open(CARS_LINK_FILE, 'w', encoding='utf-8') as f:
                f.write('\n'.join(all_links))
            self.log.info('Added %d new car links. Total: %d' % (len(new_links), len(all_links)))
        else:
            self.log.info('No new links found.')

        return new_links

    # ── Step 3: Scrape data từ links ─────────────────────────

    def scrape_data(self):
        """
        Đọc danh sách URL từ file links, scrape những URL chưa có trong data.
        Kết quả được ghi thêm (prepend) vào file data JSON.
        """
        self.log.info('=== SCRAPE DATA MODE ===')

        existing_data_urls = self._load_existing_urls()
        all_links = self._load_existing_crawled_links()

        # Chỉ scrape những link chưa có trong data
        links_to_scrape = [url for url in all_links if url not in existing_data_urls]
        self.log.info('Links to scrape: %d / %d' % (len(links_to_scrape), len(all_links)))

        if not links_to_scrape:
            self.log.info('Nothing to scrape.')
            return [], []

        crawled_items = []
        failed_items = []

        # Load data cũ
        existing_data = []
        if os.path.exists(CARS_DATA_FILE) and not is_file_empty(CARS_DATA_FILE):
            with open(CARS_DATA_FILE, 'r', encoding='utf-8') as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    existing_data = []

        progress = tqdm(links_to_scrape, desc='Scraping cars', unit='car')
        for url in progress:
            progress.set_postfix(failed=len(failed_items))
            time.sleep(0.5)

            try:
                car = BonBanhScraper(url, self.session).extract()
            except TimeoutError:
                self.log.warning('Timeout, retrying: %s' % url)
                time.sleep(10)
                try:
                    car = BonBanhScraper(url, self.session).extract()
                except Exception as e:
                    self.log.error('Retry failed %s: %s' % (url, str(e)))
                    failed_items.append(url)
                    continue
            except Exception as e:
                self.log.error('Error scraping %s: %s' % (url, str(e)))
                failed_items.append(url)
                continue

            crawled_items.append(car)

        # Ghi data mới vào đầu (mới nhất trước), giữ data cũ phía sau
        all_data = crawled_items + existing_data
        with open(CARS_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=4, ensure_ascii=False)

        with open(FAILED_ITEMS_FILE, 'w', encoding='utf-8') as f:
            json.dump(failed_items, f, indent=4, ensure_ascii=False)

        self.log.info('Scraped: %d | Failed: %d' % (len(crawled_items), len(failed_items)))
        return crawled_items, failed_items
    
    def retry_failed(self):
        self.log.info('=== RETRY FAILED MODE ===')

        if not os.path.exists(FAILED_ITEMS_FILE) or is_file_empty(FAILED_ITEMS_FILE):
            self.log.info('No failed items found.')
            return [], []

        with open(FAILED_ITEMS_FILE, 'r', encoding='utf-8') as f:
            try:
                failed_urls = json.load(f)
            except json.JSONDecodeError:
                self.log.error('Failed items file corrupted.')
                return [], []

        if not failed_urls:
            self.log.info('No failed urls.')
            return [], []

        # load existing data
        existing_data = []
        if os.path.exists(CARS_DATA_FILE) and not is_file_empty(CARS_DATA_FILE):
            with open(CARS_DATA_FILE, 'r', encoding='utf-8') as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    pass

        success_items = []
        still_failed = []

        progress = tqdm(failed_urls, desc='Retry failed cars', unit='car')

        for url in progress:
            try:
                car = BonBanhScraper(url, self.session).extract()

                success_items.append(car)

                self.log.info(
                    'Retry success: %s',
                    url
                )

            except Exception as e:
                self.log.error(
                    'Retry failed %s: %s',
                    url,
                    str(e)
                )
                still_failed.append(url)

        # prepend data mới
        if success_items:
            all_data = success_items + existing_data

            with open(CARS_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(
                    all_data,
                    f,
                    indent=4,
                    ensure_ascii=False
                )

        # update failed file
        with open(FAILED_ITEMS_FILE, 'w', encoding='utf-8') as f:
            json.dump(
                still_failed,
                f,
                indent=4,
                ensure_ascii=False
            )

        self.log.info(
            'Retry completed | Success: %d | Remaining failed: %d',
            len(success_items),
            len(still_failed)
        )

        return success_items, still_failed
    # ── Public API ────────────────────────────────────────────

    def run_crawler(self):
        """Chỉ crawl links."""
        return self.crawl_links()

    def run_scraper(self):
        """Chỉ scrape data từ links đã có."""
        return self.scrape_data()

    def run_full(self):
        """Crawl links rồi scrape data."""
        self.crawl_links()
        return self.scrape_data()
    
    def run_retry(self):
        return self.retry_failed()


# ============================================================
# ARGUMENT PARSER
# ============================================================
def parse_args():
    parser = argparse.ArgumentParser(
        description='BonBanh Car Data Tool',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '--mode',
        choices=['crawler', 'scraper', 'full', 'retry'],
        help=(
            'crawler : Chỉ thu thập URL xe\n'
            'scraper : Chỉ scrape data từ URL đã thu thập\n'
            'full    : Thu thập URL rồi scrape data\n'
            'retry   : Chỉ scrape lại data từ url đã thất bại\n'
        )
    )
    return parser.parse_args()


# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    args = parse_args()
    bot = BonBanhCrawler()

    if args.mode == 'crawler':
        bot.run_crawler()
    elif args.mode == 'scraper':
        bot.run_scraper()
    elif args.mode == 'full':
        bot.run_full()
    elif args.mode == 'retry':
        bot.run_retry()