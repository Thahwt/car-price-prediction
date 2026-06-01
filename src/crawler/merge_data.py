import pandas as pd

df_csv = pd.read_csv('data/coordinates/geomap.csv')
df_json = pd.read_json('data/bonbanh/bonbanh_used_cars.json')
df_merged = pd.merge(df_json, df_csv, on='location', how='inner')
df_merged.to_csv('merged_dataset.csv', index=False)