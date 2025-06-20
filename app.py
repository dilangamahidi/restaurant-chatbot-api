from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import numpy as np
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# Carica modello ML
try:
    model = joblib.load('restaurant_model_client.pkl')
    print("✅ ML Model loaded!")
except:
    print("❌ Model not found!")
    model = None

# Info ristorante - AGGIORNATE PER RESTORAN
RESTAURANT_INFO = {
    "name": "Restoran",
    "phone": "0764272635",
    "email": "dilangakavindu123@gmail.com",
    "address": "Aluthgoga Road, Mawella, Nakulugamuwa, Matara",
    "description": "Matara's home of authentic Sri Lankan flavor"
}

# Menu Sri Lankano
MENU = {
    "breakfast": ["String Hoppers with Curry", "Milk Rice (Kiribath)", "Coconut Roti with Sambol", "Ceylon Tea"],
    "lunch": ["Rice and Curry", "Kottu Roti", "Fried Rice", "Hoppers with Egg"],
    "dinner": ["Fish Curry", "Chicken Curry", "Seafood Platter", "Vegetarian Curry"],
    "beverages": ["King Coconut", "Ceylon Tea", "Fresh Juices", "Local Beer"]
}

def convert_day_to_number(day_name):
    """Converte nome giorno in numero per ML"""
    days = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
        'friday': 4, 'saturday': 5, 'sunday': 6,
        'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6
    }
    return days.get(str(day_name).lower(), 5)  # Default Saturday

def convert_time_to_hour(time_str):
    """Converte time string in hour per ML"""
    try:
        time_str = str(time_str).lower().strip()
        
        # Gestisce PM/AM
        if 'pm' in time_str:
            hour = int(time_str.replace('pm', '').split(':')[0].strip())
            if hour != 12:
                hour += 12
        elif 'am' in time_str:
            hour = int(time_str.replace('am', '').split(':')[0].strip())
            if hour == 12:
                hour = 0
        else:
            # Formato 24h o semplice numero
            if ':' in time_str:
                hour = int(time_str.split(':')[0])
            else:
                hour = int(time_str)
        
        # Controllo orari validi (9-21 = 9AM-9PM)
        return hour if 9 <= hour <= 21 else 19  # Default 7PM
    except:
        return 19  # Default 7PM

def parse_dialogflow_datetime(date_param, time_param):
    """
    Converte parametri date/time da Dialogflow in day_of_week e hour_of_day
    """
    try:
        # Default values
        day_of_week = 5  # Saturday
        hour_of_day = 19  # 7 PM
        
        # Parse date se presente
        if date_param:
            if isinstance(date_param, str):
                # Dialogflow può inviare "2024-12-25" o nomi giorni
                if '-' in date_param:
                    # ISO date format
                    parsed_date = datetime.fromisoformat(date_param.replace('Z', '+00:00'))
                    day_of_week = parsed_date.weekday()
                else:
                    # Nome giorno
                    day_of_week = convert_day_to_number(date_param)
        
        # Parse time se presente  
        if time_param:
            hour_of_day = convert_time_to_hour(time_param)
            
        return day_of_week, hour_of_day
        
    except Exception as e:
        print(f"Error parsing datetime: {e}")
        return 5, 19  # Default Saturday 7PM

def check_table_availability(table_number, guest_count, day_of_week, hour_of_day):
    """Usa ML model per controllare disponibilità tavolo"""
    if model is None:
        return False
    try:
        input_data = np.array([[table_number, guest_count, day_of_week, hour_of_day]])
        prediction = model.predict(input_data)[0]
        return prediction == 0  # 0 = available, 1 = occupied
    except:
        return False

def find_available_table(guest_count, day_of_week, hour_of_day):
    """
    Trova tavolo disponibile automaticamente
    NON richiede table_number dal cliente
    """
    available_tables = []
    
    # Controlla tutti i tavoli (1-20)
    for table_number in range(1, 21):
        if check_table_availability(table_number, guest_count, day_of_week, hour_of_day):
            available_tables.append(table_number)
    
    if available_tables:
        # Scegli il miglior tavolo per il numero di ospiti
        if guest_count <= 2:
            # Preferisci tavoli piccoli (1-8)
            small_tables = [t for t in available_tables if t <= 8]
            best_table = small_tables[0] if small_tables else available_tables[0]
        elif guest_count <= 4:
            # Preferisci tavoli medi (9-15)
            medium_tables = [t for t in available_tables if 9 <= t <= 15]
            best_table = medium_tables[0] if medium_tables else available_tables[0]
        else:
            # Preferisci tavoli grandi (16-20)
            large_tables = [t for t in available_tables if t >= 16]
            best_table = large_tables[0] if large_tables else available_tables[0]
        
        return {
            'available': True,
            'table_number': best_table,
            'total_available': len(available_tables)
        }
    else:
        return {
            'available': False,
            'table_number': None,
            'total_available': 0
        }

@app.route('/')
def home():
    return jsonify({
        'message': f'{RESTAURANT_INFO["name"]} API Running!', 
        'status': 'OK',
        'model_loaded': model is not None
    })

@app.route('/dialogflow-webhook', methods=['POST'])
def dialogflow_webhook():
    """Webhook principale per Dialogflow"""
    try:
        req = request.get_json()
        intent_name = req.get('queryResult', {}).get('intent', {}).get('displayName', '')
        parameters = req.get('queryResult', {}).get('parameters', {})
        
        print(f"Intent: {intent_name}, Parameters: {parameters}")
        
        if intent_name == 'check.availability':
            return handle_check_availability(parameters)
            
        elif intent_name == 'make.reservation':
            return handle_make_reservation(parameters)
            
        elif intent_name == 'show.menu':
            return handle_show_menu(parameters)
            
        elif intent_name == 'opening.hours':
            return handle_opening_hours()
            
        elif intent_name in ['restaurant.info', 'contact.info']:
            return handle_restaurant_info()
            
        elif intent_name == 'contact.human':
            return handle_contact_human()
            
        else:
            # Default welcome
            response_text = f"🍽️ Welcome to {RESTAURANT_INFO['name']}! {RESTAURANT_INFO['description']}. I can help you check availability, make reservations, view our menu, or provide information. How can I assist you?"
        
        return jsonify({'fulfillmentText': response_text})
        
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({
            'fulfillmentText': f"Sorry, I'm having technical difficulties. Please call us at {RESTAURANT_INFO['phone']}."
        })

def handle_check_availability(parameters):
    """Gestisce controllo disponibilità"""
    try:
        # Estrai parametri
        guests = parameters.get('guest_count', parameters.get('number', 2))
        date = parameters.get('date', '')
        time = parameters.get('time', '')
        
        guest_count = int(guests) if guests else 2
        
        # Converti date/time in parametri ML
        day_of_week, hour_of_day = parse_dialogflow_datetime(date, time)
        
        # Trova tavolo disponibile
        result = find_available_table(guest_count, day_of_week, hour_of_day)
        
        if result['available']:
            table_num = result['table_number']
            total = result['total_available']
            response_text = f"✅ Great! Table {table_num} is available for {guest_count} guests! ({total} tables available). Would you like to make a reservation? I'll need your name and phone number."
        else:
            response_text = f"😔 Sorry, no tables available for {guest_count} guests at that time. Would you like to try a different time? Call us at {RESTAURANT_INFO['phone']} for more options."
            
        return jsonify({'fulfillmentText': response_text})
        
    except Exception as e:
        return jsonify({'fulfillmentText': f'Error checking availability: {str(e)}'})

def handle_make_reservation(parameters):
    """Gestisce creazione prenotazione"""
    try:
        # Estrai parametri
        name = parameters.get('person', {}).get('name', '') if parameters.get('person') else ''
        phone = parameters.get('phone-number', '')
        guests = parameters.get('guest_count', parameters.get('number', 2))
        date = parameters.get('date', '')
        time = parameters.get('time', '')
        
        guest_count = int(guests) if guests else 2
        
        # Controlla parametri richiesti
        missing = []
        if not name:
            missing.append("name")
        if not phone:
            missing.append("phone number")
            
        if missing:
            return jsonify({'fulfillmentText': f"I need your {' and '.join(missing)} to complete the reservation."})
        
        # Controlla disponibilità
        day_of_week, hour_of_day = parse_dialogflow_datetime(date, time)
        result = find_available_table(guest_count, day_of_week, hour_of_day)
        
        if result['available']:
            table_num = result['table_number']
            response_text = f"🎉 Perfect {name}! I've reserved table {table_num} for {guest_count} guests. Reservation details:\n\n• Name: {name}\n• Phone: {phone}\n• Guests: {guest_count}\n• Table: {table_num}\n\nWe look forward to serving you!"
        else:
            response_text = f"😔 Sorry {name}, no tables available for {guest_count} guests at that time. Please call {RESTAURANT_INFO['phone']} for alternative times."
            
        return jsonify({'fulfillmentText': response_text})
        
    except Exception as e:
        return jsonify({'fulfillmentText': f'Error making reservation: {str(e)}'})

def handle_show_menu(parameters):
    """Gestisce visualizzazione menu"""
    menu_category = parameters.get('menu-category', '').lower()
    
    if menu_category and menu_category in MENU:
        # Categoria specifica
        items = MENU[menu_category]
        response_text = f"🍽️ {menu_category.title()} Menu:\n\n"
        for i, item in enumerate(items, 1):
            response_text += f"{i}. {item}\n"
    else:
        # Menu completo
        response_text = f"🍽️ {RESTAURANT_INFO['name']} Menu:\n\n"
        response_text += "☀️ BREAKFAST:\n"
        for item in MENU['breakfast']:
            response_text += f"• {item}\n"
        response_text += "\n🍛 LUNCH:\n"
        for item in MENU['lunch']:
            response_text += f"• {item}\n"
        response_text += "\n🌅 DINNER:\n"
        for item in MENU['dinner']:
            response_text += f"• {item}\n"
        response_text += "\n🥤 BEVERAGES:\n"
        for item in MENU['beverages']:
            response_text += f"• {item}\n"
        response_text += f"\n📞 For prices, call {RESTAURANT_INFO['phone']}"
    
    return jsonify({'fulfillmentText': response_text})

def handle_opening_hours():
    """Gestisce orari apertura"""
    response_text = f"🕐 {RESTAURANT_INFO['name']} Opening Hours:\n\n"
    response_text += "📅 Monday - Saturday: 09:00 AM - 09:00 PM\n"
    response_text += "📅 Sunday: 10:00 AM - 08:00 PM\n\n"
    response_text += f"📞 For reservations: {RESTAURANT_INFO['phone']}"
    
    return jsonify({'fulfillmentText': response_text})

def handle_restaurant_info():
    """Gestisce info ristorante"""
    response_text = f"🍽️ {RESTAURANT_INFO['name']}\n"
    response_text += f"{RESTAURANT_INFO['description']}\n\n"
    response_text += f"📍 {RESTAURANT_INFO['address']}\n"
    response_text += f"📞 {RESTAURANT_INFO['phone']}\n"
    response_text += f"📧 {RESTAURANT_INFO['email']}\n\n"
    response_text += "🕐 Mon-Sat 9AM-9PM, Sun 10AM-8PM"
    
    return jsonify({'fulfillmentText': response_text})

def handle_contact_human():
    """Gestisce contatto umano"""
    response_text = f"👨‍💼 Contact our staff:\n\n"
    response_text += f"📞 Call: {RESTAURANT_INFO['phone']}\n"
    response_text += f"📧 Email: {RESTAURANT_INFO['email']}\n"
    response_text += f"📍 Visit: {RESTAURANT_INFO['address']}\n\n"
    response_text += "Available: Mon-Sat 9AM-9PM, Sun 10AM-8PM"
    
    return jsonify({'fulfillmentText': response_text})

# Test endpoint
@app.route('/test')
def test():
    """Test endpoint per verificare funzionalità"""
    if model is None:
        return jsonify({'error': 'Model not loaded'})
    
    # Test availability
    result = find_available_table(4, 5, 19)  # 4 guests, Saturday, 7PM
    
    return jsonify({
        'model_loaded': True,
        'test_result': result,
        'restaurant': RESTAURANT_INFO['name']
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
