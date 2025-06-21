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
            
        elif intent_name == 'check.table.specific':  # 🔧 NUOVO
            return handle_check_table_specific(parameters)
            
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

def handle_check_table_specific(parameters):
    """Gestisce controllo tavolo specifico"""
    try:
        # 🔧 AGGIUNGI QUESTA LINEA PER DEBUG
        print(f"DEBUG - Raw parameters: {parameters}")
        
        def extract_value(param):
            if isinstance(param, list):
                return param[0] if param else None
            return param
        
        # Estrai parametri
        table_raw = parameters.get('table_number', parameters.get('number', ''))
        date_raw = parameters.get('date', parameters.get('day_of_week', ''))
        time_raw = parameters.get('time', parameters.get('hour_of_day', ''))
        
        # 🔧 AGGIUNGI ANCHE QUESTO
        print(f"DEBUG - Extracted raw: table={table_raw}, date={date_raw}, time={time_raw}")
        
        table_number = extract_value(table_raw)
        date = extract_value(date_raw)
        time = extract_value(time_raw)
        
        # 🔧 E QUESTO
        print(f"DEBUG - Final values: table={table_number}, date={date}, time={time}")
        
        # Valida table number
        try:
            table_num = int(table_number) if table_number else None
            if not table_num or table_num < 1 or table_num > 20:
                return jsonify({'fulfillmentText': "Please specify a table number between 1 and 20."})
        except ValueError:
            return jsonify({'fulfillmentText': "Please provide a valid table number."})
        
        # Controlla parametri mancanti
        missing = []
        if not date:
            missing.append("the date")
        if not time:
            missing.append("the time")
            
        if missing:
            missing_text = " and ".join(missing)
            return jsonify({'fulfillmentText': f"I need {missing_text} to check table {table_num} availability."})
        
        # Converti date/time per ML
        day_of_week, hour_of_day = parse_dialogflow_datetime(date, time)
        
        # Controlla tavolo specifico (usando guest_count=4 come default per il check)
        is_available = check_table_availability(table_num, 4, day_of_week, hour_of_day)
        
        if is_available:
            response_text = f"✅ Good news! Table {table_num} is available!"
        else:
            response_text = f"😔 Sorry, table {table_num} is already reserved at that time."
            
        return jsonify({'fulfillmentText': response_text})
        
    except Exception as e:
        print(f"Error in check_table_specific: {e}")
        return jsonify({'fulfillmentText': 'Sorry, error checking table availability. Please call us.'})


def handle_check_availability(parameters):
    """Gestisce controllo disponibilità - VERSIONE CORRETTA"""
    try:
        # Funzione helper per estrarre valori
        def extract_value(param):
            if isinstance(param, list):
                return param[0] if param else None
            return param
        
        # Estrai parametri gestendo liste
        guests_raw = parameters.get('guest_count', parameters.get('number', 2))
        date_raw = parameters.get('date', parameters.get('day_of_week', ''))
        time_raw = parameters.get('time', parameters.get('hour_of_day', ''))
        
        guests = extract_value(guests_raw)
        date = extract_value(date_raw)
        time = extract_value(time_raw)
        
        # Converti a int
        guest_count = int(guests) if guests else 2
        
        # Converti date/time
        day_of_week, hour_of_day = parse_dialogflow_datetime(date, time)
        
        # Trova tavolo
        result = find_available_table(guest_count, day_of_week, hour_of_day)
        
        if result['available']:
            table_num = result['table_number']
            response_text = f"✅ Great! Table {table_num} is available for {guest_count} guests! I made the reservation!"
        else:
            response_text = f"😔 Sorry, no tables available for {guest_count} guests at that time."
            
        return jsonify({'fulfillmentText': response_text})
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'fulfillmentText': 'Sorry, error checking availability. Please call us.'})

def parse_dialogflow_datetime(date_param, time_param):
    """Parse date/time da Dialogflow"""
    try:
        day_of_week = 5  # Default Saturday
        hour_of_day = 19  # Default 7PM
        
        if date_param:
            date_str = str(date_param)
            if 'T' in date_str:
                clean_date = date_str.split('T')[0]
                from datetime import datetime
                parsed_date = datetime.strptime(clean_date, '%Y-%m-%d')
                day_of_week = parsed_date.weekday()
        
        if time_param:
            time_str = str(time_param)
            if 'T' in time_str:
                time_part = time_str.split('T')[1].split('+')[0]
                hour_of_day = int(time_part.split(':')[0])
            else:
                hour_of_day = convert_time_to_hour(time_str)
        
        return day_of_week, hour_of_day
    except:
        return 5, 19
        
def handle_make_reservation(parameters):
    """Gestisce prenotazione completa - VERSIONE FORMATTATA"""
    try:
        # Estrai tutti i parametri
        def extract_value(param):
            if isinstance(param, list):
                return param[0] if param else None
            return param
        
        # Dati personali
        person_data = parameters.get('person', {})
        name = extract_value(person_data.get('name', '')) if person_data else extract_value(parameters.get('person', ''))
        phone = extract_value(parameters.get('phone_number', ''))
        email = extract_value(parameters.get('email', ''))
        
        # Dati prenotazione
        guests = extract_value(parameters.get('guest_count', parameters.get('number', 2)))
        date = extract_value(parameters.get('date', ''))
        time = extract_value(parameters.get('time', ''))
        
        guest_count = int(guests) if guests else 2
        
        # Controlla parametri mancanti
        missing = []
        if not name:
            missing.append("your full name")
        if not phone:
            missing.append("your phone number")
        if not email:
            missing.append("your email address")
        if not date:
            missing.append("the date")
        if not time:
            missing.append("the time")
            
        if missing:
            if len(missing) == 1:
                return jsonify({'fulfillmentText': f"I need {missing[0]} to complete your reservation."})
            else:
                missing_text = ", ".join(missing[:-1]) + f" and {missing[-1]}"
                return jsonify({'fulfillmentText': f"I need {missing_text} to complete your reservation."})
        
        # Controlla disponibilità
        day_of_week, hour_of_day = parse_dialogflow_datetime(date, time)
        result = find_available_table(guest_count, day_of_week, hour_of_day)
        if result['available']:
            table_num = result['table_number']
            
            response_text = f"🎉 <strong>Reservation Confirmed!</strong><br><br>"
            response_text += "📋 <strong>Details:</strong><br>"
            response_text += f"• <strong>Name:</strong> {name}<br>"
            response_text += f"• <strong>Phone:</strong> {phone}<br>"
            response_text += f"• <strong>Email:</strong> {email}<br>"
            response_text += f"• <strong>Guests:</strong> {guest_count}<br>"
            response_text += f"• <strong>Date:</strong> {date}<br>"
            response_text += f"• <strong>Time:</strong> {time}<br>"
            response_text += f"• <strong>Table:</strong> {table_num}<br><br>"
            response_text += "We look forward to serving you! We'll contact you if there are any changes.<br><br>"
            response_text += f"For any questions, call us at {RESTAURANT_INFO['phone']}."
            
        else:
            response_text = f"😔 Sorry {name}, no tables are available for {guest_count} guests at that time.<br><br>"
            response_text += "<strong>Would you like to try:</strong><br>"
            response_text += "• Different time on the same day?<br>"
            response_text += "• Different date?<br><br>"
            response_text += f"Or call us at {RESTAURANT_INFO['phone']} for more options."
            
        return jsonify({'fulfillmentText': response_text})
        
    except Exception as e:
        print(f"Error in make_reservation: {e}")
        return jsonify({'fulfillmentText': f'Sorry, there was an error processing your reservation. Please call us at {RESTAURANT_INFO["phone"]}.'})
        
def handle_show_menu(parameters):
    """Gestisce visualizzazione menu - MULTIPLE MESSAGES"""
    menu_category = parameters.get('menu-category', '').lower()
    
    if menu_category and menu_category in MENU:
        items = MENU[menu_category]
        response_text = f"🍽️ {menu_category.title()} Menu:\n\n" + "\n".join([f"{i}. {item}" for i, item in enumerate(items, 1)])
        return jsonify({'fulfillmentText': response_text})
    else:
        # Dividi in messaggi separati
        rich_response = {
            "fulfillmentText": f"🍽️ {RESTAURANT_INFO['name']} Menu:",
            "fulfillmentMessages": [
                {
                    "text": {
                        "text": [f"🍽️ {RESTAURANT_INFO['name']} Menu:"]
                    }
                },
                {
                    "text": {
                        "text": [f"☀️ BREAKFAST:\n" + "\n".join([f"• {item}" for item in MENU['breakfast']])]
                    }
                },
                {
                    "text": {
                        "text": [f"🍛 LUNCH:\n" + "\n".join([f"• {item}" for item in MENU['lunch']])]
                    }
                },
                {
                    "text": {
                        "text": [f"🌅 DINNER:\n" + "\n".join([f"• {item}" for item in MENU['dinner']])]
                    }
                },
                {
                    "text": {
                        "text": [f"🥤 BEVERAGES:\n" + "\n".join([f"• {item}" for item in MENU['beverages']])]
                    }
                },
                {
                    "text": {
                        "text": [f"📞 For prices, call {RESTAURANT_INFO['phone']}"]
                    }
                }
            ]
        }
        return jsonify(rich_response)

def handle_opening_hours():
    """Gestisce orari apertura - MULTIPLE MESSAGES"""
    rich_response = {
        "fulfillmentText": f"🕐 {RESTAURANT_INFO['name']} Opening Hours:",
        "fulfillmentMessages": [
            {
                "text": {
                    "text": [f"🕐 {RESTAURANT_INFO['name']} Opening Hours:"]
                }
            },
            {
                "text": {
                    "text": ["📅 Monday - Saturday:\n09:00 AM - 09:00 PM"]
                }
            },
            {
                "text": {
                    "text": ["📅 Sunday:\n10:00 AM - 08:00 PM"]
                }
            },
            {
                "text": {
                    "text": [f"📞 For reservations: {RESTAURANT_INFO['phone']}"]
                }
            }
        ]
    }
    return jsonify(rich_response)

def handle_restaurant_info():
    """Gestisce info ristorante - MULTIPLE MESSAGES"""
    rich_response = {
        "fulfillmentText": f"🍽️ {RESTAURANT_INFO['name']}",
        "fulfillmentMessages": [
            {
                "text": {
                    "text": [f"🍽️ {RESTAURANT_INFO['name']}"]
                }
            },
            {
                "text": {
                    "text": [f"{RESTAURANT_INFO['description']}"]
                }
            },
            {
                "text": {
                    "text": [f"📍 Address:\n{RESTAURANT_INFO['address']}"]
                }
            },
            {
                "text": {
                    "text": [f"📞 Phone:\n{RESTAURANT_INFO['phone']}"]
                }
            },
            {
                "text": {
                    "text": [f"📧 Email:\n{RESTAURANT_INFO['email']}"]
                }
            },
            {
                "text": {
                    "text": ["🕐 Hours:\nMon-Sat 9AM-9PM\nSun 10AM-8PM"]
                }
            }
        ]
    }
    return jsonify(rich_response)
    
def handle_contact_human():
    """Gestisce contatto umano - MULTIPLE MESSAGES"""
    rich_response = {
        "fulfillmentText": "👨‍💼 Contact our staff:",
        "fulfillmentMessages": [
            {
                "text": {
                    "text": ["👨‍💼 Contact our staff:"]
                }
            },
            {
                "text": {
                    "text": [f"📞 Call:\n{RESTAURANT_INFO['phone']}"]
                }
            },
            {
                "text": {
                    "text": [f"📧 Email:\n{RESTAURANT_INFO['email']}"]
                }
            },
            {
                "text": {
                    "text": [f"📍 Visit us at:\n{RESTAURANT_INFO['address']}"]
                }
            },
            {
                "text": {
                    "text": ["Available:\nMon-Sat 9AM-9PM\nSun 10AM-8PM"]
                }
            }
        ]
    }
    return jsonify(rich_response)

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

# 🔧 SPOSTA QUESTO QUI (PRIMA di if __name__)
@app.route('/ping')
def ping():
    """Keep-alive endpoint per evitare cold starts"""
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.now().isoformat(),
        'model_loaded': model is not None,
        'uptime': 'running'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
