import pandas as pd 
from preprocess.preprocess import *


data_path = "D:/car-price-prediction/data/vietnamese-car-prices-dataset.csv"
car_price_csv = pd.read_csv(data_path)
print(car_price_csv.head(5))

car_price_csv["prices"] = car_price_csv["prices"].map(process_prices)
car_price_csv["drive"] = car_price_csv["drive"].map(process_drive)
car_price_csv["doors"] = car_price_csv["doors"].map(process_doors)
car_price_csv["seats"] = car_price_csv["seats"].map(process_seats)
car_price_csv["status"] = car_price_csv["status"].map(process_status)
car_price_csv["location"] = car_price_csv["location"].map(map_location)
car_price_csv["interior_color"] = car_price_csv["interior_color"].map(process_color)
car_price_csv["exterior_color"] = car_price_csv["exterior_color"].map(process_color)
car_price_csv["transmission"] = car_price_csv["transmission"].map(process_transmission)
car_price_csv["origin"] = car_price_csv["origin"].map(process_origin)
car_price_csv["odo"] = car_price_csv["odo"].map(process_odo)
car_price_csv[["fuel", "volumne"]] = process_engine(car_price_csv["engine"])

car_price_csv = car_price_csv.drop("engine", axis = 1)
car_price_csv.to_csv("D:/car-price-prediction/data/eda_vietnamese-car-prices-dataset.csv", index=False)




