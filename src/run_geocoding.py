import pandas as pd
from preprocess.get_coordinate import get_coordinates


def process_locations():
    print("Đọc dữ liệu xe...")
    # Giả sử bạn đã có file CSV hoặc JSON chứa dữ liệu cào được
    df_cars = pd.read_json('crawler/data/bonbanh/bonbanh_used_cars.json')

    # 2. Trích xuất danh sách địa điểm không trùng lặp
    # Loại bỏ các giá trị rỗng (NaN) nếu có
    unique_locations = df_cars['location'].dropna().unique().tolist()
    print(f"Tìm thấy {len(unique_locations)} địa điểm cần xử lý.")

    # 3. Chạy API lấy tọa độ và lưu ra file CSV
    print("Đang lấy tọa độ từ OpenStreetMap:")
    get_coordinates(
        locations=unique_locations,
        save_csv=True,
        save_path='data/coordinates/geomap.csv'
    )
    print("Tọa độ đã được lưu.")


if __name__ == '__main__':
    process_locations()