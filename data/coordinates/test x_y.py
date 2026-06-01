import pandas as pd

df = pd.read_csv('geomap.csv')
# Đếm số lượng dòng có ít nhất một cột bị null
so_dong_null = df.isna().any(axis=1).sum()

print(f"Số dòng bị null là: {so_dong_null}")