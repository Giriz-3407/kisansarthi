import requests, os



def get_weather_data(city_name, WEATHER_API_KEY, lat=None, lon=None):
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        'appid': WEATHER_API_KEY,
        'units': 'metric'
    }
    if lat is not None and lon is not None:
        params['lat'] = lat
        params['lon'] = lon
    else:
        params['q'] = city_name or 'Maharashtra'
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        # Extract humidity
        humidity = data.get('main', {}).get('humidity', 'N/A')
        temperature = data['main']['temp']

        # Extract rainfall (if available)
        rainfall = data.get('rain', {}).get('1h', 0)  # Rainfall in last 1 hour (mm)
        
        return{
            "humidity": humidity,
            "rainfall": rainfall,
            "temperature" : temperature
        }
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")

# if __name__ == "__main__":
#     api_key = input("Enter your API Key: ")
#     city_name = input("Enter city name: ")
#     get_weather_data(api_key, city_name)
