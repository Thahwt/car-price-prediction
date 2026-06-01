import json

with open(r"data/bonbanh/failed_items.json",'rb') as f : 
    data = json.load(f)

print(data[:10])
