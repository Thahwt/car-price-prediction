import pandas as pd 
import time 
import numpy as np
import os
import requests 
import random  # Thêm cái này để random thời gian nghỉ
from tqdm import tqdm
from bs4 import BeautifulSoup 
from utils import * 

save_path = 'D:/car-price-prediction/data'

page_id = 1
page = f'https://bonbanh.com/oto/page,{page_id}'

# Danh sách các User-Agent phổ biến để luân phiên thay đổi
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0"
]

while page is not None: 
    # RANDOM HEADER FOR REQUEST
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Referer': np.random.choice(['https://bonbanh.com/', 'https://www.google.com/'], 1)[0],
    }
    
    response = requests.get(page, headers=headers, timeout=10)
    
    # RETRY IF BEING BANNED
    if response.status_code != 200:
        print(f"Status code: {response.status_code}. Pause for ip being banned...")
        time.sleep(60) 
        continue 
        
    page_source = response.content
    
    
    time.sleep(1)

    data = crawl_page(page_source, page_id)
    
    if page_id == 1: 
        save_csv(data, save_path)
    
    else : 
        merge_csv(data, save_path)
    
    page = get_next_page(page_source) 
    page_id += 1 