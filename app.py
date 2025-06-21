from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import numpy as np
from datetime import datetime
import os
import re
import gspread
from google.oauth2.service_account import Credentials
import json
import traceback

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

SHEET_ID = "1QTaGoxeQur4Rh03tJETcRwExbmTvU1FF6TE1v0UjuMk"

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

def extract_value(param):
    """Estrae valore da parametri Dialogflow con controlli robusti"""
    try:
        if param is None or param == '':
            return None
        elif isinstance(param, list):
            # Se è una lista, prendi il primo elemento
            first_item = param[0] if param and len(param) > 0 else None
            if isinstance(first_item, dict):
                # Se il primo elemento è un dizionario, estrai il valore
                if 'name' in first_item and first_item['name']:
                    return str(first_item['name']).strip()
                elif 'value' in first_item and first_item['value']:
                    return str(first_item['value']).strip()
                else:
                    # Prendi il primo valore non vuoto del dizionario
                    for value in first_item.values():
                        if value and str(value).strip():
                            return str(value).strip()
                    return None
            else:
                return str(first_item).strip() if first_item not in ['', None] else None
        elif isinstance(param, dict):
            # Se è un dizionario, cerca nelle chiavi comuni
            if 'name' in param and param['name']:
                return str(param['name']).strip()
            elif 'value' in param and param['value']:
                return str(param['value']).strip()
            elif len(param) == 1:
                # Se ha una sola chiave, prendi quel valore
                value = list(param.values())[0]
                return str(value).strip() if value not in ['', None] else None
            else:
                # Prendi il primo valore non vuoto
                for value in param.values():
                    if value and str(value).strip():
                        return str(value).strip()
                return None
        else:
            # Se è una stringa o altro tipo
            clean_value = str(param).strip()
            return clean_value if clean_value not in ['', 'None', 'null'] else None
    except Exception as e:
        print(f"❌ Error in extract_value: {e}")
        print(f"❌ Param type: {type(param)}, value: {param}")
        return None

# Aggiungi questa funzione che manca
def handle_check_availability(parameters):
    """Gestisce controllo disponibilità generale"""
    try:
        print(f"🔧 DEBUG - Check availability parameters: {parameters}")
        
        # Estrai parametri
        guests = extract_value(parameters.get('guest_count', parameters.get('number', parameters.get('guests', 2))))
        date = extract_value(parameters.get('day_of_week', parameters.get('date', '')))
        time = extract_value(parameters.get('hour_of_day', parameters.get('time', '')))
        
        print(f"🔧 DEBUG - Extracted: guests={guests}, date={date}, time={time}")
        
        # Controlla parametri mancanti
        missing = []
        if not guests:
            missing.append("number of guests")
        if not date:
            missing.append("the date")
        if not time:
            missing.append("the time")
            
        if missing:
            missing_text = " and ".join(missing)
            return jsonify({'fulfillmentText': f"I need {missing_text} to check availability. Please provide the missing information."})
        
        # Converti ospiti in numero
        try:
            guest_count = int(guests)
            if guest_count < 1 or guest_count > 20:
                return jsonify({'fulfillmentText': "Please specify between 1 and 20 guests."})
        except (ValueError, TypeError):
            return jsonify({'fulfillmentText': "Please provide a valid number of guests."})
        
        # Formatta data e ora per display
        try:
            formatted_date = format_date_readable(date)
            formatted_time = format_time_readable(time)
        except Exception as e:
            print(f"❌ Error formatting date/time: {e}")
            formatted_date = str(date)
            formatted_time = str(time)
        
        # Controlla disponibilità
        try:
            day_of_week, hour_of_day = parse_dialogflow_datetime(date, time)
            result = find_available_table(guest_count, day_of_week, hour_of_day)
        except Exception as e:
            print(f"❌ Error checking availability: {e}")
            return jsonify({
                'fulfillmentText': f"Sorry, I'm having trouble checking availability. Please call us at {RESTAURANT_INFO['phone']}."
            })
        
        if result['available']:
            response_text = f"✅ Great news! We have availability for {guest_count} guests on {formatted_date} at {formatted_time}.\n\n"
            response_text += f"We have {result['total_available']} tables available at that time.\n\n"
            response_text += "Would you like to make a reservation? I'll need your name, phone number, and email address."
        else:
            response_text = f"😔 Sorry, we don't have availability for {guest_count} guests on {formatted_date} at {formatted_time}.\n\n"
            response_text += "Would you like to try:\n"
            response_text += "• A different time on the same day?\n"
            response_text += "• A different date?\n\n"
            response_text += f"Or call us at {RESTAURANT_INFO['phone']} for more options."
        
        return jsonify({'fulfillmentText': response_text})
        
    except Exception as e:
        print(f"❌ Error in check_availability: {e}")
        return jsonify({'fulfillmentText': f'Sorry, error checking availability. Please call us at {RESTAURANT_INFO["phone"]}.'})

def init_google_sheets():
    """Inizializza connessione a Google Sheets"""
    try:
        # Prova prima le variabili d'ambiente (per produzione)
        google_credentials = os.environ.get('GOOGLE_CREDENTIALS')
        
        if google_credentials:
            print("🔧 DEBUG - Trovate credenziali in variabile d'ambiente")
            # In produzione: usa variabile d'ambiente
            creds_dict = json.loads(google_credentials)
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        else:
            print("🔧 DEBUG - Cercando file credentials.json locale")
            # In sviluppo locale: usa file
            if os.path.exists('credentials.json'):
                print("🔧 DEBUG - File credentials.json trovato")
                creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
            else:
                print("❌ Nessun credential trovato - Google Sheets disabilitato")
                return None
        
        print("🔧 DEBUG - Tentativo di connessione a Google Sheets...")
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID).sheet1
        print("✅ Google Sheets connesso!")
        return sheet
        
    except Exception as e:
        print(f"❌ Errore Google Sheets: {e}")
        print(f"🔧 DEBUG - Tipo errore: {type(e)}")
        return None

def save_reservation_to_sheets(reservation_data):
    """Salva prenotazione su Google Sheets"""
    try:
        sheet = init_google_sheets()
        if not sheet:
            print("❌ Impossibile connettersi a Google Sheets")
            return False
        
        # Prepara i dati per il foglio
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        row_data = [
            timestamp,
            reservation_data['name'],
            reservation_data['phone'],
            reservation_data['email'],
            reservation_data['guests'],
            reservation_data['date'],
            reservation_data['time'],
            reservation_data['table'],
            'Confirmed'
        ]
        
        # Aggiungi la riga al foglio
        sheet.append_row(row_data)
        print(f"✅ Prenotazione salvata su Google Sheets: {reservation_data['name']}")
        return True
        
    except Exception as e:
        print(f"❌ Errore salvando su Google Sheets: {e}")
        return False

def get_reservations_from_sheets():
    """Recupera tutte le prenotazioni dal foglio"""
    try:
        sheet = init_google_sheets()
        if not sheet:
            return []
        
        # Ottieni tutti i record (saltando l'header)
        records = sheet.get_all_records()
        return records
        
    except Exception as e:
        print(f"❌ Errore leggendo da Google Sheets: {e}")
        return []

def check_existing_reservation(name, phone, date, time):
    """Controlla se esiste già una prenotazione identica"""
    try:
        reservations = get_reservations_from_sheets()
        
        for reservation in reservations:
            if (reservation.get('Name', '').lower() == name.lower() and
                reservation.get('Phone', '') == phone and
                reservation.get('Date', '') == date and
                reservation.get('Time', '') == time and
                reservation.get('Status', '') == 'Confirmed'):
                return True
        return False
        
    except Exception as e:
        print(f"❌ Errore controllo duplicati: {e}")
        return False

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
    """Webhook principale per Dialogflow con controlli migliorati"""
    try:
        req = request.get_json()
        
        if not req:
            return jsonify({'fulfillmentText': 'No request data received.'})
        
        query_result = req.get('queryResult', {})
        intent = query_result.get('intent', {})
        intent_name = intent.get('displayName', '')
        parameters = query_result.get('parameters', {})
        
        print(f"🔧 Intent: {intent_name}")
        print(f"🔧 Parameters: {parameters}")
        
        if intent_name == 'make.reservation':
            return handle_make_reservation(parameters)
        elif intent_name == 'check.availability':
            return handle_check_availability(parameters)
        elif intent_name == 'check.table.specific':
            return handle_check_table_specific(parameters)
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
        print(f"❌ WEBHOOK ERROR: {e}")
        print(f"❌ TRACEBACK: {traceback.format_exc()}")
        
        return jsonify({
            'fulfillmentText': f"I'm experiencing technical difficulties. Please call us at {RESTAURANT_INFO['phone']} for immediate assistance."
        })
        
def handle_check_table_specific(parameters):
    """Gestisce controllo tavolo specifico"""
    try:
        print(f"🔧 DEBUG - Raw parameters: {parameters}")
        
        # 🔧 MIGLIORA ESTRAZIONE NUMERO TAVOLO
        # Prova tutte le possibili chiavi per il numero del tavolo
        table_raw = None
        possible_table_keys = ['table_number', 'number', 'table', 'table_num', 'num']
        
        for key in possible_table_keys:
            if key in parameters and parameters[key]:
                table_raw = parameters[key]
                print(f"🔧 DEBUG - Found table in key '{key}': {table_raw}")
                break
        
        if not table_raw:
            print(f"🔧 DEBUG - No table found, trying extract_value on all keys")
            for key in possible_table_keys:
                extracted = extract_value(parameters.get(key, ''))
                if extracted:
                    table_raw = extracted
                    print(f"🔧 DEBUG - Extracted table from '{key}': {table_raw}")
                    break
        
        # Estrai anche date e time
        date_raw = parameters.get('date', parameters.get('day_of_week', ''))
        time_raw = parameters.get('time', parameters.get('hour_of_day', ''))
        
        print(f"🔧 DEBUG - Extracted raw: table={table_raw}, date={date_raw}, time={time_raw}")
        
        # Estrai valori con extract_value
        table_number = extract_value(table_raw)
        date = extract_value(date_raw)
        time = extract_value(time_raw)
        
        print(f"🔧 DEBUG - Final values: table={table_number}, date={date}, time={time}")
        
        # 🔧 MIGLIORA CONVERSIONE NUMERO TAVOLO
        try:
            if table_number is None or table_number == '':
                return jsonify({'fulfillmentText': "Please specify which table number you'd like to check (1-20)."})
            
            # Converti, gestendo vari formati
            table_str = str(table_number).strip().lower()
            
            # Rimuovi parole comuni
            table_str = table_str.replace('table', '').replace('number', '').replace('#', '').strip()
            
            # Converti parole in numeri se necessario
            word_to_num = {
                'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
                'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
                'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
                'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20
            }
            
            if table_str in word_to_num:
                table_num = word_to_num[table_str]
            else:
                table_num = int(float(table_str))  # Gestisce anche numeri decimali
            
            print(f"🔧 DEBUG - Converted table number: {table_num}")
            
            # Valida range tavolo
            if table_num < 1 or table_num > 20:
                return jsonify({'fulfillmentText': "Please specify a table number between 1 and 20."})
                
        except (ValueError, TypeError) as e:
            print(f"🔧 DEBUG - Error converting table '{table_number}': {e}")
            return jsonify({'fulfillmentText': "Please provide a valid table number (1-20)."})
        
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
        
        print(f"🔧 DEBUG - ML input: table={table_num}, guests=4, day={day_of_week}, hour={hour_of_day}")
        
        # Controlla tavolo specifico (usando guest_count=4 come default per il check)
        is_available = check_table_availability(table_num, 4, day_of_week, hour_of_day)
        
        print(f"🔧 DEBUG - Table {table_num} availability: {is_available}")
        
        # Formatta data e ora per la risposta
        try:
            formatted_date = format_date_readable(date)
            formatted_time = format_time_readable(time)
        except Exception as e:
            print(f"❌ Error formatting date/time: {e}")
            formatted_date = str(date)
            formatted_time = str(time)
        
        if is_available:
            response_text = f"✅ Good news! Table {table_num} is available on {formatted_date} at {formatted_time}!"
        else:
            response_text = f"😔 Sorry, table {table_num} is already reserved on {formatted_date} at {formatted_time}."
            
        return jsonify({'fulfillmentText': response_text})
        
    except Exception as e:
        print(f"❌ Error in check_table_specific: {e}")
        import traceback
        print(f"❌ TRACEBACK: {traceback.format_exc()}")
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
    """Gestisce prenotazione completa con controlli robusti - MULTIPLE MESSAGES"""
    try:
        print(f"🔧 DEBUG - RAW PARAMETERS: {parameters}")
        
        # Estrai parametri con controlli robusti
        name = extract_value(parameters.get('name', parameters.get('person', '')))
        phone = extract_value(parameters.get('phone_number', parameters.get('phone', '')))
        email = extract_value(parameters.get('email', ''))
        
        # 🔧 MIGLIORA ESTRAZIONE NUMERO OSPITI
        # Prova tutte le possibili chiavi per il numero di ospiti
        guests_raw = None
        possible_guest_keys = ['guest_count', 'guests', 'number', 'people', 'party_size', 'num_guests']
        
        for key in possible_guest_keys:
            if key in parameters and parameters[key]:
                guests_raw = parameters[key]
                print(f"🔧 DEBUG - Found guests in key '{key}': {guests_raw}")
                break
        
        if not guests_raw:
            print(f"🔧 DEBUG - No guests found, trying extract_value on all keys")
            for key in possible_guest_keys:
                extracted = extract_value(parameters.get(key, ''))
                if extracted:
                    guests_raw = extracted
                    print(f"🔧 DEBUG - Extracted guests from '{key}': {guests_raw}")
                    break
        
        # Se ancora non trovato, usa default
        if not guests_raw:
            guests_raw = 2
            print(f"🔧 DEBUG - Using default guests: {guests_raw}")
        
        guests = extract_value(guests_raw)
        
        date = extract_value(parameters.get('day_of_week', parameters.get('date', '')))
        time = extract_value(parameters.get('hour_of_day', parameters.get('time', '')))
        
        print(f"🔧 DEBUG - Extracted: name={name}, phone={phone}, email={email}, guests={guests}, date={date}, time={time}")
        
        # 🔧 MIGLIORA CONVERSIONE NUMERO OSPITI
        try:
            if guests is None or guests == '':
                guest_count = 2  # Default
                print(f"🔧 DEBUG - Using default guest count: {guest_count}")
            else:
                # Prova a convertire, gestendo vari formati
                guest_str = str(guests).strip().lower()
                
                # Rimuovi parole comuni
                guest_str = guest_str.replace('guests', '').replace('people', '').replace('persons', '').strip()
                
                # Converti parole in numeri
                word_to_num = {
                    'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
                    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
                }
                
                if guest_str in word_to_num:
                    guest_count = word_to_num[guest_str]
                else:
                    guest_count = int(float(guest_str))  # Gestisce anche numeri decimali
                
                print(f"🔧 DEBUG - Converted guest count: {guest_count}")
                
        except (ValueError, TypeError) as e:
            print(f"🔧 DEBUG - Error converting guests '{guests}': {e}")
            guest_count = 2  # Fallback
        
        # Valida range ospiti
        if guest_count < 1 or guest_count > 20:
            return jsonify({
                'fulfillmentText': f"I can accommodate between 1 and 20 guests. You requested {guest_count} guests. Please specify a number between 1 and 20."
            })
        
        # Valida gli altri parametri (escludi guests dalla validazione dato che l'abbiamo già gestito)
        validation_errors = []
        
        # Nome
        if not name or len(str(name).strip()) < 2:
            validation_errors.append("a valid full name (at least 2 characters)")
        
        # Telefono
        if not phone:
            validation_errors.append("your phone number")
        elif not re.match(r'^[\d\s\-\+\(\)]+$', str(phone)):
            validation_errors.append("a valid phone number")
        
        # Email
        if not email:
            validation_errors.append("your email address")
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', str(email)):
            validation_errors.append("a valid email address")
        
        # Data
        if not date:
            validation_errors.append("the reservation date")
        
        # Ora
        if not time:
            validation_errors.append("the reservation time")
        
        if validation_errors:
            if len(validation_errors) == 1:
                error_text = validation_errors[0]
            elif len(validation_errors) == 2:
                error_text = f"{validation_errors[0]} and {validation_errors[1]}"
            else:
                error_text = f"{', '.join(validation_errors[:-1])}, and {validation_errors[-1]}"
            
            return jsonify({
                'fulfillmentText': f"I need {error_text} to complete your reservation. Please provide the missing information."
            })
        
        # Formatta data e ora
        try:
            formatted_date = format_date_readable(date)
            formatted_time = format_time_readable(time)
        except Exception as e:
            print(f"❌ Error formatting date/time: {e}")
            formatted_date = str(date)
            formatted_time = str(time)
        
        # Controllo duplicati
        try:
            if check_existing_reservation(name, phone, formatted_date, formatted_time):
                return jsonify({
                    'fulfillmentText': f"⚠️ You already have a reservation for {formatted_date} at {formatted_time}. Contact us to modify it."
                })
        except Exception as e:
            print(f"❌ Error checking duplicates: {e}")
            # Continua comunque
        
        # Controlla disponibilità
        try:
            day_of_week, hour_of_day = parse_dialogflow_datetime(date, time)
            result = find_available_table(guest_count, day_of_week, hour_of_day)
        except Exception as e:
            print(f"❌ Error checking availability: {e}")
            return jsonify({
                'fulfillmentText': f"Sorry, I'm having trouble checking availability. Please call us at {RESTAURANT_INFO['phone']}."
            })
        
        if result['available']:
            table_num = result['table_number']
            
            # Prepara dati per salvataggio
            reservation_data = {
                'name': str(name).strip(),
                'phone': str(phone).strip(),
                'email': str(email).strip(),
                'guests': guest_count,
                'date': formatted_date,
                'time': formatted_time,
                'table': table_num
            }
            
            # Salva su Google Sheets
            try:
                sheets_saved = save_reservation_to_sheets(reservation_data)
            except Exception as e:
                print(f"❌ Error saving to sheets: {e}")
                sheets_saved = False
            
            # Risposta di successo con multiple messages
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
            
            # Aggiungi messaggio se sheets non funziona
            if not sheets_saved:
                rich_response["fulfillmentMessages"].append({
                    "text": {
                        "text": ["📝 Note: Our staff will contact you to confirm details."]
                    }
                })
            
            return jsonify(rich_response)
            
        else:
            # Nessuna disponibilità - MULTIPLE MESSAGES
            rich_response = {
                "fulfillmentText": f"😔 Sorry {name}, no tables available",
                "fulfillmentMessages": [
                    {
                        "text": {
                            "text": [f"😔 Sorry {name}, no tables are available for {guest_count} guests at that time."]
                        }
                    },
                    {
                        "text": {
                            "text": ["Would you like to try:\n• Different time on the same day?\n• Different date?"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"Or call us at {RESTAURANT_INFO['phone']} for more options."]
                        }
                    }
                ]
            }
            return jsonify(rich_response)
            
    except Exception as e:
        print(f"❌ CRITICAL ERROR in make_reservation: {e}")
        import traceback
        print(f"❌ TRACEBACK: {traceback.format_exc()}")
        
        # Messaggio di errore più specifico
        error_message = f"I'm sorry, there was a technical issue processing your reservation. "
        error_message += f"Please call us directly at {RESTAURANT_INFO['phone']} and we'll be happy to help you immediately."
        
        return jsonify({'fulfillmentText': error_message})
        
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
