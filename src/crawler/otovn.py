from selenium.webdriver import Edge
from selenium.webdriver.common.by import By 
from bs4 import BeautifulSoup
import time 
import re
import requests
from base import BaseClass
from header import HEADERS
import os 
import json 
import argparse
from tqdm import tqdm
from common.check import is_file_empty
from crawler import Crawler
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException



DATA_DIR = 'data/otovn'
BRANDS_LINK_FILE = f'{DATA_DIR}/otovn_brands_link.txt'
CARS_LINK_FILE = f'{DATA_DIR}/otovn_cars_links.txt'
CARS_DATA_FILE = f'{DATA_DIR}/otovn_used_cars.json'
FAILED_ITEMS_FILE = f'{DATA_DIR}/otovn_failed_items.json'
SITE_URL = 'https://oto.com.vn/mua-ban-xe'
BASE_URL = 'https://oto.com.vn/'


class OtovnScraper(BaseClass):
    def __init__(self, url, session=None):
        super().__init__()
        self.url = url
        self.session = session or Edge()
        self.log.info('Connecting to %s' % self.url)
        self.session.get(url)
        time.sleep(1)
        self.soup = BeautifulSoup(self.session.page_source, 'html.parser')

    def _car_name_normalizer(self, brand, model, name):
        name = name.lower().replace(brand.lower(), '').replace(model.lower(), '')
        return " ".join(name.split()[:-1]) or None

    def _get_date(self, date_str):
        date = re.search(r'\d{1,2}/\d{1,2}/\d{4}', date_str)
        return date.group() if date else date_str

    def _extract_price(self, price_str):
        normalized = price_str.lower().strip().split()
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
        fuel = fuel_str.split()[-1]
        fuel_map = {'xăng': 'gasoline', 'dầu': 'diesel', 'điện': 'electric', 'hybrid': 'hybrid'}
        return fuel_map.get(fuel, fuel)

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


    def _extract_header_info(self):
        model_tags = self.soup.select('div.head-breadcrumb.mt-15 > a')
        name_tags = self.soup.select('h1.title-detail')
        date_tags = self.soup.select('span.date')
        price_tags = self.soup.select('span.price')

        brand = model_tags[1].text.strip().lower().replace('mua ', '' ).split()[0]
        model = model_tags[2].text.strip().lower().replace('mua ', '' ).split()[0]
        name = self._car_name_normalizer(brand, model, name_tags[0].text.strip())
        price = self._extract_price(price_tags[0].text.strip())
        date = self._get_date(date_tags[0].text.strip())

        return name, brand, model, date, price

    def _extract_detail_info(self):
        info_tags = self.soup.select('div.box-info-detail li')
        info_contains = [(tag.text.lower().replace(': ', ':').split(':')) for tag in info_tags]
        
        schema ={
            'year': None,
            'status': None,
            'odo': None,
            'origin': None,
            'style': None,
            'transmission': None,
            'engine': None,
            'volume': None,
            'exterior_color': None,
            'interior_color': None,
            'seats': None,
            'doors': None,
            'drive': None,
            'location' : None
        }

        for info in info_contains: 
            if 'năm' in info[0] : 
                schema['year'] = int(info[1])
            elif 'tình trạng' in info[0] : 
                schema['status'] = self._extract_status(info[1])
            elif 'km' in info[0] : 
                schema['odo'] = self._extract_odo(info[1])
            elif 'xuất xứ' in info[0] : 
                schema['origin'] = self._extract_origin(info[1])
            elif 'kiểu dáng' in info[0] : 
                schema['style'] = info[1].lower()
            elif 'hộp số' in info[0] : 
                schema['transmission'] = self._extract_transmission(info[1])
            elif 'nhiên liệu' in info[0] : 
                fuel = self._extract_fuel(info[1])
                schema['engine'] = fuel
                schema['volume'] = None
            elif 'tỉnh' in info[0]:
                schema['location'] = info[1]

        return schema


    def extract(self):
        trim, brand, model, date, price = self._extract_header_info()
        detail_info = self._extract_detail_info()
        return {
            'url': self.url,
            'brand': brand,
            'model': model,
            'trim': trim,
            'date': date,
            'price': price,
            **detail_info
        }

class OtovnCrawler(Crawler):
    def __init__(self):
        super().__init__()
        self.log.info('Connecting to %s' % BASE_URL)
        self.session = Edge()
        self.session.get(SITE_URL)
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
        brands = []

        transparent = self.soup.select('ul.list.listMake li[makeid]')

        black_list = ['/mua-ban-xe', 
                      'javascript:void(0)',
                      '/mua-ban-xe-hang-khac', 
                      '/mua-ban-xe-hang-khac-dong-khac']
        for item in transparent:
            if item.find('a')['href'] not in black_list:
                brands.append(BASE_URL + item.find('a')['href'])

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
            
            # Lấy trang cuối cùng
            wait = WebDriverWait(self.session, 5)
            while True:

                try:
                    button = wait.until(
                        EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, 'span.btn-loadmore')
                        )
                    )

                    self.session.execute_script("""
                        arguments[0].scrollIntoView({
                            block: 'center'
                        });
                    """, button)

                    self.session.execute_script(
                        "arguments[0].click();",
                        button
                    )

                except:
                    print('Done')
                    break

            soup = BeautifulSoup(self.session.page_source, 'html.parser')
            car_items = soup.select('div.item-car div.photo')

            for car in car_items:
                car_href = car.find('a')['href']
                car_url = BASE_URL + car_href if car_href.startswith('/') else car_url

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
                car = OtovnScraper(url, self.session).extract()
            except TimeoutError:
                self.log.warning('Timeout, retrying: %s' % url)
                time.sleep(10)
                try:
                    car = OtovnScraper(url, self.session).extract()
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
        choices=['crawler', 'scraper', 'full'],
        help=(
            'crawler : Chỉ thu thập URL xe\n'
            'scraper : Chỉ scrape data từ URL đã thu thập\n'
            'full    : Thu thập URL rồi scrape data'
        )
    )
    return parser.parse_args()


# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    args = parse_args()
    bot = OtovnCrawler()

    if args.mode == 'crawler':
        bot.run_crawler()
    elif args.mode == 'scraper':
        bot.run_scraper()
    elif args.mode == 'full':
        bot.run_full()

