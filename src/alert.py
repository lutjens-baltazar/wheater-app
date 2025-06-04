import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from urllib.parse import quote
from weather_models import OpenWeatherModel, WindDirection, OpenMeteoModel
from persistence import ModelStorage


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

# Whatsapp keys
WHATSAPP_PHONE_2 = os.getenv("WHATSAPP_PHONE_2")
WHATSAPP_API_KEY_2 = os.getenv("WHATSAPP_API_KEY_2")
WHATSAPP_PHONE_3 = os.getenv("WHATSAPP_PHONE_3")
WHATSAPP_API_KEY_3 = os.getenv("WHATSAPP_API_KEY_3")
WHATSAPP_PHONE_4 = os.getenv("WHATSAPP_PHONE_4")
WHATSAPP_API_KEY_4 = os.getenv("WHATSAPP_API_KEY_4")
WHATSAPP_PHONE_5 = os.getenv("WHATSAPP_PHONE_5")
WHATSAPP_API_KEY_5 = os.getenv("WHATSAPP_API_KEY_5")
WHATSAPP_PHONE_6 = os.getenv("WHATSAPP_PHONE_6")
WHATSAPP_API_KEY_6 = os.getenv("WHATSAPP_API_KEY_6")


# Configuration
LAT = "-40.9286360" 
LON = "-73.3587130"
WIND_SPEED_MIN = 2.5  # in m/s
WIND_SPEED_MAX = 5.0  # in m/s
WIND_DIRECTION_MIN = 230 # west 
WIND_DIRECTION_MAX = 280 #n north west

# Initialize weather models
weather_models = [
    OpenMeteoModel('best_match'),
    OpenMeteoModel('gfs_seamless'),
    OpenMeteoModel('ecmwf_ifs04'),
    OpenMeteoModel('metno_nordic'),
    OpenMeteoModel('gem_seamless')
]


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

def translate_wind_direction(direction):
    if 250 <= float(direction) <= 280:
        return "dirección escuela"
    elif 220 <= float(direction) < 250:
        return "dirección plaza"
    return f"dirección {direction}°"

def verify_prediction_accuracy(prediction, historical_data):
    data = historical_data.get('data', {}).get('wind', {})
    wind_speeds = data.get('wind_speed', {}).get('list', {})
    wind_directions = data.get('wind_direction', {}).get('list', {})
    
    pred_timestamp = int(prediction.timestamp.timestamp())
    
    for his_timestamp, his_speed in wind_speeds.items():
        his_timestamp = int(his_timestamp)
        if abs(his_timestamp - pred_timestamp) <= 1800:  # 30 minutes tolerance
            his_direction = wind_directions.get(str(his_timestamp))
            if his_direction:
                speed_accurate = abs(float(his_speed) - prediction.speed) <= (prediction.speed * 0.2)
                direction_accurate = abs(float(his_direction) - prediction.direction) <= 30
                return speed_accurate and direction_accurate
    return False


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
    """Send message through CallMeBot WhatsApp API to all configured recipients"""
    successful_sends = 0
    failed_sends = 0
    
    # List of recipient configurations
    recipients = [
        (WHATSAPP_PHONE, WHATSAPP_API_KEY),
        (WHATSAPP_PHONE_2, WHATSAPP_API_KEY_2),
        (WHATSAPP_PHONE_3, WHATSAPP_API_KEY_3),
        (WHATSAPP_PHONE_4, WHATSAPP_API_KEY_4),
        (WHATSAPP_PHONE_5, WHATSAPP_API_KEY_5),
        (WHATSAPP_PHONE_6, WHATSAPP_API_KEY_6)
    ]
    
    for phone, api_key in recipients:
        if not phone or not api_key:
            continue
            
        try:
            params = {
                'phone': phone,
                'text': message,
                'apikey': api_key
            }
            response = requests.get(WHATSAPP_API_URL, params=params)
            print(f"WhatsApp Message Status Code for {phone}: {response.status_code}")
            
            if response.status_code == 200:
                successful_sends += 1
            else:
                failed_sends += 1
                
        except Exception as e:
            print(f"Error sending WhatsApp message to {phone}: {e}")
            failed_sends += 1
    
    print(f"\n📱 Resumen de envíos:")
    print(f"✅ Enviados correctamente: {successful_sends}")
    print(f"❌ Fallidos: {failed_sends}")
    
    return successful_sends > 0

def main():
    mensajes = []
    model_predictions = {}
    storage = ModelStorage()
    
    stored_stats = storage.load_stats()
    for model in weather_models:
        if model.model_name in stored_stats:
            model.from_dict(stored_stats[model.model_name])
    print("\n📊 Iniciando verificación de pronósticos...")
    print("==========================================")
    
    # Get predictions from all models
    for model in weather_models:
        try:
            
            predictions = model.get_forecast(LAT, LON)
            future_alerts = []
            
            for pred in predictions:
                if pred.timestamp <= datetime.now() + timedelta(days=3):
                    if check_wind_conditions(pred.speed, pred.direction):
                        print(f"  ⚠️ Alerta encontrada:")
                        print(f"    Modelo: {model.model_name}")
                        print(f"    Hora: {pred.timestamp}")
                        print(f"    Velocidad: {pred.speed:.1f} m/s")
                        print(f"    Dirección: {pred.direction}° ({translate_wind_direction(pred.direction)})")
                        future_alerts.append(pred)
            
            if future_alerts:
                model_predictions[model.model_name] = future_alerts
                
        except Exception as e:
            print(f"\n❌ Error obteniendo pronóstico de {model.model_name}: {e}")
    
    # Get historical data and verify accuracy
    historical_data = get_historical_data()
    
    # Update model accuracy with historical data
    for model in weather_models:
        model.total_predictions = 0
        model.accuracy_count = 0
        if model.model_name in model_predictions:
            predictions = model_predictions[model.model_name]
            for pred in predictions:
                if pred.timestamp <= datetime.now():
                    model.total_predictions += 1
                    if verify_prediction_accuracy(pred, historical_data):
                        model.accuracy_count += 1
    # Save updated stats to storage
    new_stats = {}
    for model in weather_models:
        new_stats[model.model_name] = model.to_dict()
    
    storage.save_stats(new_stats)
    
    
    # Generate messages for each model
    for model_name, predictions in model_predictions.items():
        if predictions:
            model = next((m for m in weather_models if m.model_name == model_name), None)
            accuracy = model.get_accuracy_percentage() if model else 0
            
            mensajes.append(f"\n⚠️ ALERTAS DE {model_name}:")
            mensajes.append(f"📊 Precisión del modelo: {accuracy:.1f}%")
            
            for pred in predictions:
                mensajes.append(
                    f"  - {pred.timestamp.strftime('%d/%m/%Y %H:%M')}: "
                    f"Velocidad del viento {pred.speed:.1f} m/s, "
                    f"{translate_wind_direction(pred.direction)}"
                )
    
    # Combine all messages into one text
    mensaje_completo = "\n".join(mensajes)
    
    # Print and send the message
    if mensajes:
        print("\nResumen de Alertas:")
        print("==================")
        print(mensaje_completo)
        
        if send_whatsapp_message(mensaje_completo):
            print("\n✅ Mensaje de WhatsApp enviado correctamente")
        else:
            print("\n❌ Error al enviar mensaje de WhatsApp")
    else:
        print("\nNo se encontraron alertas de viento peligroso.")
        send_whatsapp_message("No se encontraron alertas de viento peligroso en las próximas 72 horas.")

    return mensaje_completo
if __name__ == "__main__":
    main()
