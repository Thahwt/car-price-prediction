import pandas as pd
from api import GeoCoder

def get_coordinates(locations, save_path='data/coordinates/geomap.csv', save_csv=False):
    geocoder = GeoCoder()
    
    coordinates = {loc : geocoder.get_coordinates(loc) for loc in locations}
    
    if save_csv:
        df = pd.DataFrame(coordinates).T.reset_index()
        df.columns = ["location", "latitude", "longitude"]
        df.to_csv(save_path, index=False)
    
    return coordinates

