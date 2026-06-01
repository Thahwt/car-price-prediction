import requests 
from time import sleep

class GeoCoder : 
    def __init__(self):
        self.base_url =  "https://nominatim.openstreetmap.org/search"
        self.params = {"q" : None, "format" : "jsonv2", "limit" : 1}
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3", "Accept-Language": "en-US,en;q=0.5"}
    

    def get_coordinates(self, str_place):
        str_place = str_place.lower().strip()
        self.params["q"] = str_place
        response = requests.get(self.base_url, params=self.params, headers=self.headers)
        data = response.json()
        sleep(1)
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])

        return None, None


if __name__ == "__main__":
    geocoder = GeoCoder()
    print(geocoder.get_coordinates("ho chi minh"))
