import json
import pandas as pd

def process_prices(price : str) -> int:
    """
    Hàm dùng để biển đổi giá trị price từ string -> int
    """
    normalized_price = price.lower().strip() 
    normalized_price_pairs = normalized_price.split()
    price_pairs = [] 
    for i in range(1, len(normalized_price_pairs), 2) :
        price_pairs.append((int(normalized_price_pairs[i-1]), normalized_price_pairs[i]))
    

    prices = 0 
    for pair in price_pairs : 
        price, unit = pair 
        if unit == 'triệu' : 
            prices += price * 1_000_000
        elif unit == 'tỷ' or unit == 'tỉ' : 
            prices += price * 1_000_000_000
        else : 
            return None
    return prices

def map_location(location : str) -> str : 
    """
    Hàm này dùng để map lại tỉnh thành sau sáp nhập
    """
    JSON_PATH = "D:/car-price-prediction/data/new_provinces_map.json"
    with open (JSON_PATH, 'r', encoding = 'utf-8') as f:
        province_map = json.load(f)

    return province_map[location]

def process_seats(seat : str) -> int : 
    """
    Hàm này dùng để biển đổi seat từ str -> int
    """
    return seat.strip().split()[0] 

def process_doors(door : str) -> int : 
    """
    Hàm này dùng để biển đổi door từ str -> int
    """
    return door.strip().split()[0] 

def process_origin(origin : str) -> str : 
    """
    Hàm này dùng để chuyển origin sang tiếng anh
    """
    if origin.lower() == "lắp ráp trong nước" :
        return "assemble"
    elif origin.lower() == "nhập khẩu" :
        return "import"
    return None

def process_odo(odo: str) -> int:
    """
    Hàm này chuyển số km về float
    """
    if not pd.isna(odo) : 
        odo = odo.split()[0]
        odo = odo.replace(',', '')
        return int(odo)
    return 0

def process_transmission(transmission : str) -> str :
    """
    Hàm này dùng để chuyển transmission sang tiếng anh 
    """
    if transmission.lower() == "số tự động" : 
        return "auto"
    elif transmission.lower() == "số sàn" :
        return "manual"
    return None

def process_status(status : str) -> str : 
    status = status.lower() 
    if status == "xe đã dùng" : 
        return "used"
    elif status == "xe mới" : 
        return "new"
    return None 

def process_engine(engine) :
    """
    Hàm này để trích xuất thông tin động cơ thành loại nhiên liệu và dung tích
    """
    def process_fuel(fuel : str) : 
        if fuel.lower() == "xăng" : 
            return "gasonline"
        elif fuel.lower() == "dầu" : 
            return "diesel" 
        elif fuel.lower() == "điện" :
            return "electric"
        return None
    extracted_engine = engine.str.lower().str.strip().str.replace(" l", "").str.split(expand=True)
    extracted_engine.columns = ["fuel", "volumn"]
    extracted_engine["fuel"] = extracted_engine["fuel"].map(process_fuel)
    return extracted_engine 



def process_color(color: str):
    if color is None:
        return "other"
    
    color = color.strip().lower()

    if color == "đen":
        return "black"
    elif color == "trắng":
        return "white"
    elif color == "kem":
        return "cream"
    elif color == "đỏ":
        return "red"
    elif color == "xanh":
        return "blue"
    elif color == "vàng":
        return "yellow"
    elif color == "cam":
        return "orange"
    elif color == "hồng":
        return "pink"
    elif color == "tím":
        return "purple"
    elif color == "nâu":
        return "brown"
    elif color == "xám":
        return "gray"
    elif color == "ghi":
        return "silver_gray"
    elif color == "bạc":
        return "silver"
    elif color == "cát":
        return "beige"
    elif color == "đồng":
        return "copper"
    elif color == "nhiều màu":
        return "multicolor"
    else:
        return "other"


def process_drive(drive : str) -> str : 
    """
    Hàm này dùng để lấy tên viết tắt hệ dẫn động
    """
    return drive.lower().strip().split()[0] 

def process_description(text : str) -> list : 
    """
    Hàm này dùng để chuẩn hóa văn bản. 
    """
    pass 
