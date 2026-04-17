import json

# Dữ liệu map đã được viết hoa chữ cái đầu
tinh_thanh_map = {
    "Hà Nội": "TP. Hà Nội",
    "Thừa Thiên Huế": "TP. Huế",
    "Lai Châu": "Lai Châu",
    "Quảng Ninh": "Quảng Ninh",
    "Thanh Hóa": "Thanh Hoá",
    "Nghệ An": "Nghệ An",
    "Điện Biên": "Điện Biên",
    "Sơn La": "Sơn La",
    "Lạng Sơn": "Lạng Sơn",
    "Hà Tĩnh": "Hà Tĩnh",
    "Cao Bằng": "Cao Bằng",
    "Tuyên Quang": "Tuyên Quang", "Hà Giang": "Tuyên Quang",
    "Lào Cai": "Lào Cai", "Yên Bái": "Lào Cai",
    "Thái Nguyên": "Thái Nguyên", "Bắc Kạn": "Thái Nguyên",
    "Phú Thọ": "Phú Thọ", "Vĩnh Phúc": "Phú Thọ", "Hòa Bình": "Phú Thọ",
    "Bắc Ninh": "Bắc Ninh", "Bắc Giang": "Bắc Ninh",
    "Hưng Yên": "Hưng Yên", "Thái Bình": "Hưng Yên",
    "Hải Phòng": "TP. Hải Phòng", "Hải Dương": "TP. Hải Phòng",
    "Ninh Bình": "Ninh Bình", "Nam Định": "Ninh Bình", "Hà Nam": "Ninh Bình",
    "Quảng Bình": "Quảng Trị", "Quảng Trị": "Quảng Trị",
    "Đà Nẵng": "TP. Đà Nẵng", "Quảng Nam": "TP. Đà Nẵng",
    "Quảng Ngãi": "Quảng Ngãi", "Kon Tum": "Quảng Ngãi",
    "Gia Lai": "Gia Lai", "Bình Định": "Gia Lai",
    "Khánh Hòa": "Khánh Hòa", "Ninh Thuận": "Khánh Hòa",
    "Lâm Đồng": "Lâm Đồng", "Bình Thuận": "Lâm Đồng", "Đắk Nông": "Lâm Đồng",
    "Đắk Lắk": "Đắk Lắk", "Phú Yên": "Đắk Lắk",
    "Hồ Chí Minh": "TP. Hồ Chí Minh", "TP.HCM": "TP. Hồ Chí Minh",
    "Bình Dương": "TP. Hồ Chí Minh", "Bà Rịa Vũng Tàu": "TP. Hồ Chí Minh",
    "Đồng Nai": "Đồng Nai", "Bình Phước": "Đồng Nai",
    "Tây Ninh": "Tây Ninh", "Long An": "Tây Ninh",
    "Cần Thơ": "TP. Cần Thơ", "Sóc Trăng": "TP. Cần Thơ", "Hậu Giang": "TP. Cần Thơ",
    "Vĩnh Long": "Vĩnh Long", "Bến Tre": "Vĩnh Long", "Trà Vinh": "Vĩnh Long",
    "Đồng Tháp": "Đồng Tháp", "Tiền Giang": "Đồng Tháp",
    "Cà Mau": "Cà Mau", "Bạc Liêu": "Cà Mau",
    "An Giang": "An Giang", "Kiên Giang": "An Giang"
}

# Ghi ra file JSON
with open('map_tinh_thanh.json', 'w', encoding='utf-8') as f:
    json.dump(tinh_thanh_map, f, ensure_ascii=False, indent=4)