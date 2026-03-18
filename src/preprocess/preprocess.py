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
print(process_prices("198 triệu"))
def map_location(location : str) -> str : 
    """
    Hàm này dùng để map lại tỉnh thành sau sáp nhập
    """
    pass

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
