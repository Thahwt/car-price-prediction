import pandas as pd 
import time 
import os
import requests 
from tqdm import tqdm
from bs4 import BeautifulSoup 


base_url = "https://bonbanh.com"

def get_next_page(page_source): 
    parser = BeautifulSoup(page_source, 'html.parser')
    time.sleep(1)
    nav_page = parser.find('div', class_='navpage').find('div', class_='navpage')
    bbl_tag = nav_page.find_all('span')
    current_page = None 
    for nav in bbl_tag : 
        if "pactive" in nav.get('class', []):
            current_page = int(nav.text.strip())
        if current_page is not None and int(nav.text.strip()) > current_page  : 
            return nav["url"]
    return None


def get_product_info(page_source):
    parser = BeautifulSoup(page_source, 'html.parser') 
    gray_box = parser.find('div', class_ = 'gray-box')
    
    div_tags_1 = gray_box.find_all('li', class_='car-item row1') 
    div_tags_2 = gray_box.find_all('li', class_='car-item row2')
    div_tags = div_tags_1 + div_tags_2
    print("Lengths : ", len(div_tags_1), len(div_tags_2))
    
    a_tags = [div.find('a').get('href') for div in div_tags]
    url_lists = [f'{base_url}/{a_tag}' for a_tag in a_tags]
    car_names = [div.find('div', class_='cb2_02').text.strip() for div in div_tags]
    prices = [div.find('div', class_='cb3').text.strip() for div in div_tags]
    location = [div.find('div', class_='cb4').text.strip() for div in div_tags]
    
    return car_names, prices, location, url_lists

def extract_data(page_source): 
    # FIELDS TO SCRAPE
    year=None 
    status=None
    odo=None
    origin=None
    style=None
    transmission=None
    engine=None
    exterior_color=None
    interior_color=None
    seats=None
    doors=None
    drive=None
    description=None
    brand=None
    model=None

    # SCRAPING
    parser = BeautifulSoup(page_source, 'html.parser')
    breadcum = parser.find('div', class_='breadcrum')
    brand = breadcum.find_all('span', attrs={"itemprop": "itemListElement"})[2].find('a').text.strip()
    model = breadcum.find_all('span', attrs={"itemprop": "itemListElement"})[3].find('a').text.strip()
    print(brand)
    
    car_details, description = parser.find_all('div', class_='box_car_detail')
    
    configuration = car_details.find_all('div', attrs={'id' : 'mail_parent'})
    
    for config in configuration : 
        if config.find('div', class_='label').text.strip() == 'Năm sản xuất:' : 
            year = (config.find('div', class_='txt_input') or config.find('div', class_='inputbox')).text.strip()
        if config.find('div', class_='label').text.strip() == 'Tình trạng:' : 
            status = (config.find('div', class_='txt_input') or config.find('div', class_='inputbox')).text.strip()
        if config.find('div', class_='label').text.strip() == 'Xuất xứ:' : 
            origin = (config.find('div', class_='txt_input') or config.find('div', class_='inputbox')).text.strip()
        if config.find('div', class_='label').text.strip() == 'Kiểu dáng:' : 
            style = (config.find('div', class_='txt_input') or config.find('div', class_='inputbox')).text.strip()
        if config.find('div', class_='label').text.strip() == 'Hộp số:' : 
            transmission = (config.find('div', class_='txt_input') or config.find('div', class_='inputbox')).text.strip()
        if config.find('div', class_='label').text.strip() == 'Động cơ:' : 
            engine = (config.find('div', class_='txt_input') or config.find('div', class_='inputbox')).text.strip()
        if config.find('div', class_='label').text.strip() == 'Màu ngoại thất:' : 
            exterior_color = (config.find('div', class_='txt_input') or config.find('div', class_='inputbox')).text.strip()
        if config.find('div', class_='label').text.strip() == 'Màu nội thất:' : 
            interior_color = (config.find('div', class_='txt_input') or config.find('div', class_='inputbox')).text.strip()
        if config.find('div', class_='label').text.strip() == 'Số chỗ ngồi:' : 
            seats = (config.find('div', class_='txt_input') or config.find('div', class_='inputbox')).text.strip()
        if config.find('div', class_='label').text.strip() == 'Số cửa:' : 
            doors = (config.find('div', class_='txt_input') or config.find('div', class_='inputbox')).text.strip()
        if config.find('div', class_='label').text.strip() == 'Dẫn động:' : 
            drive = (config.find('div', class_='txt_input') or config.find('div', class_='inputbox')).text.strip()
        if config.find('div', class_='label').text.strip() == 'Số Km đã đi:' : 
            odo = (config.find('div', class_='txt_input') or config.find('div', class_='inputbox')).text.strip()
     


    description = description.find('div', class_='des_txt').text.strip() 
    
    return [brand, model, year, status, odo, origin, style, transmission, engine, exterior_color, interior_color, seats, doors, drive, description]

def save_csv(csv_file, path) : 
    csv_file.to_csv(f'{path}/vietnamese-car-prices-dataset.csv', index=False)

def merge_csv(csv_file, path) : 
    csv_saved = pd.read_csv(f'{path}/vietnamese-car-prices-dataset.csv')
    merge_csv = pd.concat([csv_saved, csv_file], axis=0).reset_index(drop=True)
    save_csv(merge_csv, path)

def crawl_page(page_source, index): 
    dataframe = pd.DataFrame()
    car_names, prices, location, urls = get_product_info(page_source)
    dataframe['names'] = car_names
    dataframe['prices'] = prices 
    dataframe['location'] = location
    print(dataframe)

 
    rows = []
    for url in tqdm(urls, desc=f'Crawling {len(urls)} items for page {index}') : 
        page = requests.get(url).content
        time.sleep(1)
        row = extract_data(page)
        rows.append(row)
        print(row)
        
    dataframe_ = pd.DataFrame(rows) 
    dataframe_.columns = ['brand', 'model', 'year', 'status', 'odo', 'origin', 'style', 'transmission', 'engine', 'exterior_color', 'interior_color', 'seats', 'doors', 'drive', 'description']
    merge_csv = pd.concat([dataframe, dataframe_], axis=1)
    return merge_csv

