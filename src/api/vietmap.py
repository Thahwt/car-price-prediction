import requests
import os
import json
import csv
import re
import unicodedata
import argparse
from time import sleep
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class UnifiedGeoCoder:
    def __init__(self, log_path="../../data/geo_log.json"):

        # =========================
        # API CONFIG
        # =========================
        self.osm_url = os.getenv("OSM_BASE_PATH")
        self.vietmap_url = os.getenv("VIETMAP_BASE_PATH")
        self.vietmap_api_key = os.getenv("VIETMAP_API_KEY")

        self.log_path = log_path

        self.osm_headers = self.vietmap_header= {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3", 
                                                 "Accept-Language": "en-US,en;q=0.5"}

        self.osm_params = {
            "q": None,
            "format": "jsonv2",
            "limit": 1
        }

        self.province_data = self._load_province_csv("./../data/data/provinces_coordinates.json")


    def _preprocess(self, s):
        s = str(s).lower().strip()
        s = unicodedata.normalize("NFC", s)
        s = re.sub(r"\s+", " ", s)
        return s

    def _log(self, input_text, result, source):

        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "input": input_text,
            "result": result,
            "source": source
        }

        try:
            if os.path.exists(self.log_path):
                with open(self.log_path, "r", encoding="utf-8") as f:
                    logs = json.load(f)
            else:
                logs = []

            logs.append(log_entry)

            with open(self.log_path, "w", encoding="utf-8") as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print("Log error:", e)


    def _osm_geocode(self, place: str):

        try:
            self.osm_params["q"] = place

            response = requests.get(
                self.osm_url,
                params=self.osm_params,
                headers=self.osm_headers,
                timeout=10
            )

            data = response.json()

            sleep(1)

            if data:
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                return lat, lon

        except Exception:
            pass

        return None

    def _vietmap_geocode(self, place: str):

        try:
            params = {
                "api-version": "1.1",
                "apikey": self.vietmap_api_key,
                "text": place
            }

            response = requests.get(
                self.vietmap_url,
                params=params,
                timeout=10,
                headers=self.vietmap_header
            )

            data = response.json()

            features = data.get("data", {}).get("features", [])

            if features:
                lon, lat = features[0]["geometry"]["coordinates"]
                return lat, lon

        except Exception:
            pass

        return None

    def _province_fallback(self, text):

        for province_name, coord in self.province_data.items():

            if province_name in text:
                return coord

        return None

    def get_coordinates(self, place: str):
        raw_input = place
        place = self._preprocess(place)
        print(place)

        print(self.province_data)
        print("osm")
        result = self._osm_geocode(place)

        if result:
            self._log(raw_input, result, "osm")
            return result

        print("vietmap")
        result = self._vietmap_geocode(place)

        if result:
            self._log(raw_input, result, "vietmap")
            return result

        print("fallback")
        result = self._province_fallback(place)

        if result:
            self._log(raw_input, result, "province_fallback")
            return result

        self._log(raw_input, (None, None), "failed")

        return None, None

    def _load_province_csv(self, path):

        data = {}

        if not os.path.exists(path):
            return data

        with open(path, "r", encoding="utf-8") as f:

            reader = csv.DictReader(f)

            for row in reader:
                data[row["province"].lower()] = (
                    float(row["lat"]),
                    float(row["lon"])
                )

        return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", type=str, required=True)
    args = parser.parse_args()

    geocoder = UnifiedGeoCoder()

    lat, lon = geocoder.get_coordinates(args.address)
    print("Latitude:", lat)
    print("Longitude:", lon)