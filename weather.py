import os
import requests
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class WeatherAPI:
    BASE_URL = "http://api.openweathermap.org/data/2.5"
    
    def __init__(self):
        self.api_key = os.environ.get('OPENWEATHERMAP_API_KEY')
        if not self.api_key:
            raise ValueError("OpenWeatherMap API key not configured")

    def validate_location(self, location: str) -> Optional[Dict]:
        """Validate location exists and return coordinates."""
        try:
            params = {
                'q': location,
                'appid': self.api_key,
                'limit': 1
            }
            response = requests.get(f"{self.BASE_URL}/weather", params=params)
            response.raise_for_status()
            data = response.json()
            
            return {
                'lat': data['coord']['lat'],
                'lon': data['coord']['lon'],
                'name': data['name'],
                'country': data.get('sys', {}).get('country', '')
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Error validating location: {str(e)}")
            return None

    def get_weather_data(self, location: str, num_days: Optional[int] = None,
                        start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
        """Get weather forecast for a location."""
        try:
            # First validate the location
            location_data = self.validate_location(location)
            if not location_data:
                raise ValueError(f"Invalid location: {location}")

            # Determine date range
            if start_date and end_date:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                end = datetime.strptime(end_date, '%Y-%m-%d')
                days = (end - start).days + 1
            else:
                days = min(num_days or 5, 14)  # Default to 5 days, max 14
                start = datetime.now()

            params = {
                'lat': location_data['lat'],
                'lon': location_data['lon'],
                'appid': self.api_key,
                'units': 'imperial',  # Use imperial units (Fahrenheit)
                'exclude': 'minutely,alerts'
            }

            response = requests.get(f"{self.BASE_URL}/forecast", params=params)
            response.raise_for_status()
            data = response.json()

            # Process and format the weather data
            weather_data = []
            current_date = start.date()
            
            # Group forecast data by day
            daily_data = {}
            for item in data['list']:
                forecast_time = datetime.fromtimestamp(item['dt'])
                if forecast_time.date() < current_date or len(daily_data) >= days:
                    continue
                
                date_str = forecast_time.strftime('%Y-%m-%d')
                if date_str not in daily_data:
                    daily_data[date_str] = {
                        'date': date_str,
                        'temperature': item['main']['temp'],
                        'condition': item['weather'][0]['main'],
                        'precipitation': item['pop'] * 100,  # Convert to percentage
                        'hourly': []
                    }
                
                # Add hourly data
                daily_data[date_str]['hourly'].append({
                    'time': forecast_time.strftime('%H:%M'),
                    'temperature': item['main']['temp'],
                    'condition': item['weather'][0]['main'],
                    'precipitation': item['pop'] * 100
                })

            # Convert to list and sort by date
            weather_data = list(daily_data.values())
            weather_data.sort(key=lambda x: x['date'])

            return weather_data

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching weather data: {str(e)}")
            raise ValueError(f"Error fetching weather data: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise ValueError(f"Unexpected error: {str(e)}")
