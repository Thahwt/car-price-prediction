import pandas as pd 

dataset = pd.read_csv('data/vietnamese-car-prices-dataset.csv')

print(dataset.info())

print(dataset.head(10))
