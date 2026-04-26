import pandas as pd 

def drop_duplicates(data : pd.DataFrame, stat=True) : 
    if stat : 
        print("Total duplicated rows : ", data.duplicated().sum())
    data = data.drop_duplicates()
    return data