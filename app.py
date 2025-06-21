from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import numpy as np
from datetime import datetime
import os
import re

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
            
        elif intent_name == 'check.table.specific':
            return handle_check_table_specific(parameters)
            
        elif intent_name == 'make.reservation':
            return handle_make_reservation(parameters)
            
        elif intent_name == 'show.menu':
            return handle_show_menu(parameters)
            
        elif intent_name == 'opening.hours':
            return handle_opening_hours()
            
        elif intent_name in ['restaurant.info']:
            return handle_restaurant_info()
            
        elif intent_name == 'contact.human':
            return handle_contact_human()
            
        elif intent_name == 'restaurant.location':
            return handle_restaurant_location()
            
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

def format_date_readable(date_string):
    """
    Converte data da formato ISO in formato leggibile
    """
    if not date_string:
        return ""
    
    try:
        # Se è in formato ISO (2025-06-23T12:00:00+02:00)
        if 'T' in str(date_string):
            date_part = str(date_string).split('T')[0]
            date_obj = datetime.strptime(date_part, '%Y-%m-%d')
        else:
            # Se è solo la data (2025-06-23)
            date_obj = datetime.strptime(str(date_string), '%Y-%m-%d')
        
        # Formatta come "Monday, June 23, 2025"
        return date_obj.strftime('%A, %B %d, %Y')
    except:
        # Se non riesce a parsare, ritorna l'originale
        return str(date_string)

def format_time_readable(time_string):
    """
    Converte ora da formato ISO in formato leggibile
    """
    if not time_string:
        return ""
    
    try:
        # Se è in formato ISO completo (2025-06-22T12:00:00+02:00)
        if 'T' in str(time_string):
            time_part = str(time_string).split('T')[1].split('+')[0]
            hour = int(time_part.split(':')[0])
            minute = int(time_part.split(':')[1])
        else:
            # Se è solo l'ora (12:00 o 12)
            time_str = str(time_string).strip()
            if ':' in time_str:
                hour = int(time_str.split(':')[0])
                minute = int(time_str.split(':')[1]) if len(time_str.split(':')) > 1 else 0
            else:
                hour = int(time_str)
                minute = 0
        
        # Converte in formato 12h con AM/PM
        if hour == 0:
            formatted_time = f"12:{minute:02d} AM"
        elif hour < 12:
            formatted_time = f"{hour}:{minute:02d} AM"
        elif hour == 12:
            formatted_time = f"12:{minute:02d} PM"
        else:
            formatted_time = f"{hour-12}:{minute:02d} PM"
            
        return formatted_time
    except:
        # Se non riesce a parsare, ritorna l'originale
        return str(time_string)
        
def handle_make_reservation(parameters):
    """Gestisce prenotazione completa - MULTIPLE MESSAGES"""
    try:
        # 🔧 DEBUG - Stampa tutti i parametri ricevuti
        print(f"🔧 DEBUG - RAW PARAMETERS: {parameters}")
        
        # Funzione helper migliorata per estrarre valori
        def extract_value(param):
            if isinstance(param, list):
                return param[0] if param else None
            elif isinstance(param, dict):
                # Se è un dict, cerca chiavi comuni come 'name', 'value', etc.
                if 'name' in param:
                    return param['name']
                elif 'value' in param:
                    return param['value']
                elif len(param) == 1:
                    # Se ha una sola chiave, prendi il valore
                    return list(param.values())[0]
                else:
                    # Se è un dict complesso, convertilo in stringa leggibile
                    return str(param)
            return param
        
        # Funzione specifica per il nome che gestisce formati complessi
        def extract_name(name_param):
            if not name_param:
                return ''
            
            # Se è già una stringa semplice
            if isinstance(name_param, str):
                return name_param.strip()
            
            # Se è una lista
            if isinstance(name_param, list):
                if len(name_param) > 0:
                    return extract_name(name_param[0])
                return ''
            
            # Se è un dizionario
            if isinstance(name_param, dict):
                # Cerca chiavi comuni per il nome
                for key in ['name', 'given-name', 'first-name', 'value', 'text']:
                    if key in name_param:
                        result = name_param[key]
                        if isinstance(result, str):
                            return result.strip()
                        elif isinstance(result, dict) and 'name' in result:
                            return result['name'].strip()
                
                # Se nessuna chiave comune, prova a estrarre il primo valore stringa
                for value in name_param.values():
                    if isinstance(value, str) and value.strip():
                        return value.strip()
            
            # Fallback: converti in stringa e pulisci
            name_str = str(name_param)
            # Rimuovi caratteri comuni di formattazione dict/list
            import re
            cleaned = re.sub(r"[{}\[\]'\":]", "", name_str)
            cleaned = re.sub(r"\s+", " ", cleaned)  # Normalizza spazi
            return cleaned.strip()
        
        # 🔧 DEBUG - Controlla ogni singolo parametro
        print(f"🔧 DEBUG - name raw: {parameters.get('name')}")
        print(f"🔧 DEBUG - name type: {type(parameters.get('name'))}")
        
        # Estrai dati personali con parsing migliorato
        name = extract_name(parameters.get('name', ''))
        phone = extract_value(parameters.get('phone_number', ''))
        email = extract_value(parameters.get('email', ''))
        
        # 🔧 DEBUG - Risultato parsing nome
        print(f"🔧 DEBUG - name parsed: '{name}'")
        
        # Dati prenotazione
        guests = extract_value(parameters.get('guest_count', parameters.get('number', 2)))
        date = extract_value(parameters.get('day_of_week', parameters.get('date', '')))
        time = extract_value(parameters.get('hour_of_day', parameters.get('time', '')))
        
        # 🔧 FORMATTA DATA E ORA (senza pulizia dati)
        formatted_date = format_date_readable(date) if date else date
        formatted_time = format_time_readable(time) if time else time
        
        guest_count = int(guests) if guests else 2
        
        # Controlla parametri mancanti
        missing = []
        if not name or name.lower() in ['none', 'null', '']:
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
            missing_text = ", ".join(missing[:-1]) + f" and {missing[-1]}" if len(missing) > 1 else missing[0]
            return jsonify({'fulfillmentText': f"I need {missing_text} to complete your reservation."})
        
        # Controlla disponibilità
        day_of_week, hour_of_day = parse_dialogflow_datetime(date, time)
        print(f"🔧 DEBUG - PARSED: day_of_week={day_of_week}, hour_of_day={hour_of_day}")
        
        result = find_available_table(guest_count, day_of_week, hour_of_day)
        print(f"🔧 DEBUG - AVAILABILITY RESULT: {result}")
        
        if result['available']:
            table_num = result['table_number']
            
            # Usa multiple messages invece di HTML
            rich_response = {
                "fulfillmentText": "🎉 Reservation Confirmed!",
                "fulfillmentMessages": [
                    {
                        "text": {
                            "text": ["🎉 Reservation Confirmed!"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"👤 Name: {name}"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"📞 Phone: {phone}"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"📧 Email: {email}"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"👥 Number of guests: {guest_count}"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"📅 Date: {formatted_date}"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"🕐 Time: {formatted_time}"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"🪑 Table assigned: {table_num}"]
                        }
                    },
                    {
                        "text": {
                            "text": ["✅ Your reservation is confirmed!"]
                        }
                    }
                ]
            }
            return jsonify(rich_response)
            
        else:
            # Nessuna disponibilità
            rich_response = {
                "fulfillmentText": f"😔 Sorry {name}, no tables available",
                "fulfillmentMessages": [
                    {
                        "text": {
                            "text": [f"😔 Sorry {name}, no tables are available for {guest_count} guests at that time."]
                        }
                    }
                ]
            }
            return jsonify(rich_response)
            
    except Exception as e:
        print(f"🔧 ERROR in make_reservation: {e}")
        print(f"🔧 ERROR type: {type(e)}")
        import traceback
        print(f"🔧 TRACEBACK: {traceback.format_exc()}")
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
        ]
    }
    return jsonify(rich_response)

def handle_restaurant_location():
    """Gestisce richiesta location ristorante - MULTIPLE MESSAGES"""
    rich_response = {
        "fulfillmentText": f"📍 {RESTAURANT_INFO['name']} Location:",
        "fulfillmentMessages": [
            {
                "text": {
                    "text": [f"📍 {RESTAURANT_INFO['name']} Location:"]
                }
            },
            {
                "text": {
                    "text": [f"🏠 Address:\n{RESTAURANT_INFO['address']}"]
                }
            },
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
