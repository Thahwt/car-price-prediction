import pandas as pd 
from preprocess.preprocess import *


data_path = "D:/car-price-prediction/data/vietnamese-car-prices-dataset.csv"
car_price_csv = pd.read_csv(data_path)
print(car_price_csv.head(5))

car_price_csv["prices"] = car_price_csv["prices"].map(process_prices)
car_price_csv["drive"] = car_price_csv["drive"].map(process_drive)
car_price_csv["doors"] = car_price_csv["doors"].map(process_doors)
car_price_csv["seats"] = car_price_csv["seats"].map(process_seats)

car_price_csv.to_csv("D:/car-price-prediction/data/eda_vietnamese-car-prices-dataset.csv", index=False)




