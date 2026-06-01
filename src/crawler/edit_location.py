import json
import re  # Import thư viện biểu thức chính quy (Regular Expression)

with open('data/bonbanh/bonbanh_used_cars_patched.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for car in data:
    # Sửa lại điều kiện để kiểm tra chắc chắn key 'location' có tồn tại trong dict
    if 'location' in car and isinstance(car['location'], str):
        # Biểu thức r'[,;\-\|]' sẽ cắt chuỗi khi gặp dấu phẩy (,), chấm phẩy (;), gạch nối (-), hoặc gạch đứng (|)
        # Bạn có thể thêm các ký tự khác vào trong cặp ngoặc vuông [] nếu muốn
        parts = re.split(r'[,;\-\|]', car['location'])

        # Lấy phần tử cuối cùng sau khi cắt và xóa khoảng trắng 2 đầu
        car['location'] = parts[-1].strip()

        loc = car['location'].strip()

        # 2. Lọc bỏ các cụm từ lặp lại liên tiếp
        # Regex này sẽ tìm các cụm từ lặp lại (dù là 1 chữ hay nhiều chữ) đứng cạnh nhau
        loc = re.sub(r'\b(.+?)(?:\s+\1)+\b', r'\1', loc, flags=re.IGNORECASE)

        car['location'] = loc

with open('data/bonbanh/bonbanh_used_cars.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)