from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import requests

class WindDirection(Enum):
    SCHOOL = "dirección escuela"
    PLAZA = "dirección plaza"

@dataclass
class WindPrediction:
    speed: float
    direction: float
    timestamp: datetime
    model_name: str

class OpenMeteoModel:
    MODELS = {
        'best_match': 'Best match of multiple models',
        'ecmwf_ifs04': 'ECMWF IFS',
        'metno_nordic': 'MET Norway Nordic system',
        'gfs_seamless': 'GFS Global',
        'gem_seamless': 'GEM Global'
    }
    
    def __init__(self, model_name):
        self.model_name = model_name
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.accuracy_count = 0
        self.total_predictions = 0
    
    def to_dict(self):
        return {
            'model_name': self.model_name,
            'accuracy_count': self.accuracy_count,
            'total_predictions': self.total_predictions
        }
        
    def from_dict(self, data):
        self.accuracy_count = data.get('accuracy_count', 0)
        self.total_predictions = data.get('total_predictions', 0)
    
    def get_forecast(self, lat, lon):
        params = {
            'latitude': lat,
            'longitude': lon,
            'hourly': 'windspeed_10m,winddirection_10m',
            'windspeed_unit': 'ms',
            'forecast_days': 3,
            'model': self.model_name
        }
        
        try:
            print(f"\n🌐 Making request for {self.model_name}...")
            print(f"URL: {self.base_url}")
            print(f"Parameters: {params}")
            
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            print(f"Response status: {response.status_code}")
            print(f"First hour of data:")
            if 'hourly' in data:
                for i in range(min(3, len(data['hourly']['time']))):  # Show first 3 entries
                    print(f"  Time: {data['hourly']['time'][i]}")
                    print(f"  Wind Speed: {data['hourly']['windspeed_10m'][i]} m/s")
                    print(f"  Wind Direction: {data['hourly']['winddirection_10m'][i]}°")
                    print("  ---")
            predictions = []
            times = data['hourly'].get('time', [])
            speeds = data['hourly'].get('windspeed_10m', [])
            directions = data['hourly'].get('winddirection_10m', [])
            
            if not (len(times) == len(speeds) == len(directions)):
                raise ValueError(f"Inconsistent data lengths for model {self.model_name}")
            
            for time, speed, direction in zip(times, speeds, directions):
                if speed is not None and direction is not None:
                    try:
                        predictions.append(WindPrediction(
                            speed=float(speed),
                            direction=float(direction),
                            timestamp=datetime.fromisoformat(time),
                            model_name=f"OpenMeteo-{self.model_name}"
                        ))
                    except (ValueError, TypeError) as e:
                        print(f"Warning: Skipping invalid data point in {self.model_name}: {e}")
                        continue
                    
            return predictions
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed for {self.model_name}: {str(e)}")
        except (KeyError, ValueError) as e:
            raise Exception(f"Invalid data format for {self.model_name}: {str(e)}")
class WeatherModel:
    def __init__(self, name, api_key=None):
        self.name = name
        self.api_key = api_key
        self.accuracy_count = 0
        self.total_predictions = 0
        
    def get_accuracy_percentage(self):
        if self.total_predictions == 0:
            return 0
        return (self.accuracy_count / self.total_predictions) * 100

    def translate_direction(self, degrees):
        if 270 <= degrees <= 300:  # Más al norte
            return WindDirection.SCHOOL
        elif 240 <= degrees < 270:  # Más al sur
            return WindDirection.PLAZA
        return None

class OpenWeatherModel(WeatherModel):
    def get_forecast(self, lat, lon):
        url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={self.api_key}"
        response = requests.get(url)
        data = response.json()
        predictions = []
        
        for item in data['list']:
            predictions.append(WindPrediction(
                speed=item['wind']['speed'],
                direction=item['wind']['deg'],
                timestamp=datetime.fromtimestamp(item['dt']),
                model_name=self.name
            ))
        return predictions