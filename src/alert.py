import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from urllib.parse import quote

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
EXTERNAL_API_KEY = os.getenv("EXTERNAL_API_KEY")
EXTERNAL_API_URL = os.getenv("EXTERNAL_API_URL")
EXTERNAL_APPLICATION_KEY = os.getenv("EXTERNAL_APPLICATION_KEY")
MAC_ADDRESS = os.getenv("MAC_ADDRESS")
BASE_URL = os.getenv("BASE_URL")
WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL")
WHATSAPP_PHONE = os.getenv("WHATSAPP_PHONE")
WHATSAPP_API_KEY = os.getenv("WHATSAPP_API_KEY")


# Configuration
LAT = "-40.9286360" 
LON = "-73.3587130"
WIND_SPEED_MIN = 3.0  # in m/s
WIND_SPEED_MAX = 5.0  # in m/s
WIND_DIRECTION_MIN = 240  # South
WIND_DIRECTION_MAX = 300  # West

def get_weather_forecast():
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={LAT}&lon={LON}&appid={OPENWEATHER_API_KEY}"
    response = requests.get(url)
    print(response)
    return response.json()

def get_historical_data():
    # Calculate date range for last 24 hours
    end_date = datetime.now()
    start_date = end_date - timedelta(days=1)
    
    # Format dates for API and encode them
    start_date_str = quote(start_date.strftime("%Y-%m-%d %H:%M:%S"))
    end_date_str = quote(end_date.strftime("%Y-%m-%d %H:%M:%S"))
    
    # Build query URL directly to match the working example
    url = f"{BASE_URL}?application_key={EXTERNAL_APPLICATION_KEY}&api_key={EXTERNAL_API_KEY}&mac={MAC_ADDRESS}&start_date={start_date_str}&end_date={end_date_str}&cycle_type=30min&call_back=wind&wind_speed_unitid=6"
    
    # Make request
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        print(f"URL: {url}")
        return response.json()
    except Exception as e:
        print(f"Error making request: {e}")
        return {"code": -1, "msg": str(e)}

def check_wind_conditions(wind_speed, wind_direction):
    return (WIND_SPEED_MIN <= float(wind_speed) <= WIND_SPEED_MAX and 
            WIND_DIRECTION_MIN <= float(wind_direction) <= WIND_DIRECTION_MAX)


def process_historical_data(historical_data):
    if historical_data.get('code') != 0:
        print("Error getting historical data")
        return False

    data = historical_data.get('data', {}).get('wind', {})
    wind_speeds = data.get('wind_speed', {}).get('list', {})
    wind_directions = data.get('wind_direction', {}).get('list', {})

    # Get timestamps for the last 24 hours
    now = datetime.now()
    day_ago = now - timedelta(days=1)
    day_ago_timestamp = int(day_ago.timestamp())

    alerts = []
    for timestamp, speed in wind_speeds.items():
        timestamp = int(timestamp)
        if timestamp >= day_ago_timestamp:
            print(f"Timestamp: {timestamp}, Speed: {speed}")
            direction = wind_directions.get(str(timestamp))
            if direction and check_wind_conditions(speed, direction):
                alert_time = datetime.fromtimestamp(timestamp)
                alerts.append(alert_time)

    return alerts

def send_whatsapp_message(message):
    """Send message through CallMeBot WhatsApp API"""
    try:
        params = {
            'phone': WHATSAPP_PHONE,
            'text': message,
            'apikey': WHATSAPP_API_KEY
        }
        response = requests.get(WHATSAPP_API_URL, params=params)
        print(f"WhatsApp Message Status Code: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending WhatsApp message: {e}")
        return False


def main():
    # Initialize messages list
    mensajes = []
    
    # Check forecast for next 3 days
    forecast_data = get_weather_forecast()
    future_alerts = []
    
    for item in forecast_data['list']:
        date = datetime.fromtimestamp(item['dt'])
        if date <= datetime.now() + timedelta(days=3):
            wind_speed = item['wind']['speed']
            wind_direction = item['wind']['deg']
            
            if check_wind_conditions(wind_speed, wind_direction):
                future_alerts.append({
                    'time': date,
                    'speed': wind_speed,
                    'direction': wind_direction
                })

    # Check historical data for the last 24 hours
    historical_data = get_historical_data()
    past_alerts = process_historical_data(historical_data)
    
    # Compose messages
    if future_alerts:
        mensajes.append("\n⚠️ ALERTAS DE PRONÓSTICO:")
        for alert in future_alerts:
            mensajes.append(
                f"  - {alert['time'].strftime('%d/%m/%Y %H:%M')}: "
                f"Velocidad del viento {alert['speed']:.1f} m/s, "
                f"dirección {alert['direction']}°"
            )
        mensajes.append(
            f"\n⚠️ ADVERTENCIA: Se encontraron {len(future_alerts)} horas "
            f"con condiciones de viento peligrosas en los próximos 3 días!"
        )
    
    if past_alerts:
        mensajes.append("\n🔍 VERIFICADO: Condiciones de viento peligrosas ocurrieron en:")
        for alert_time in past_alerts:
            mensajes.append(
                f"  - {alert_time.strftime('%d/%m/%Y %H:%M')}"
            )
        mensajes.append(
            f"\n📢 AVISO: Se encontraron {len(past_alerts)} instancias de "
            f"condiciones de viento peligrosas en las últimas 24 horas!"
        )

    # Combine all messages into one text
    mensaje_completo = "\n".join(mensajes)
    
    # Print the complete message
    # Print the complete message
    if mensajes:
        print("\nResumen de Alertas:")
        print("==================")
        print(mensaje_completo)
        
        # Send WhatsApp message if there are alerts
        if send_whatsapp_message(mensaje_completo):
            print("\n✅ Mensaje de WhatsApp enviado correctamente")
        else:
            print("\n❌ Error al enviar mensaje de WhatsApp")
    else:
        print("\nNo se encontraron alertas de viento peligroso.")

    return mensaje_completo
if __name__ == "__main__":
    main()