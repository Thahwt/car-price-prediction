import json 
import pandas as pd 
from vietmap import UnifiedGeoCoder

JSON_FILE=r"E:\car-price-prediction\data\provinces.json"

with open(JSON_FILE, "rb") as f: 
    data = json.load(f)


normalized_loc = {k.lower() : v.lower() for k, v in data.items()}

print(normalized_loc)

gecoder = UnifiedGeoCoder() 
provinces_location : list[dict] = []

for old, new in list(normalized_loc.items()): 
    key = old 
    lat, lon = gecoder.get_coordinates(old)
    provinces_location.append({"province" : old, "lat" : lat, "lon" : lon})

df = pd.DataFrame(provinces_location)
df.to_csv("E:\car-price-prediction\data\provinces_coordinates.json")

