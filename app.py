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

def delete_reservation_from_sheets(phone, date, time):
    """Elimina completamente una prenotazione dal Google Sheets"""
    try:
        sheet = init_google_sheets()
        if not sheet:
            return False
        
        # Ottieni tutti i dati
        all_values = sheet.get_all_values()
        
        # Trova la riga da eliminare
        row_to_delete = None
        for i, row in enumerate(all_values):
            if (len(row) >= 9 and 
                row[2].strip() == str(phone).strip() and  # Phone column
                row[5].strip() == str(date).strip() and   # Date column  
                row[6].strip() == str(time).strip() and   # Time column
                row[8].strip() == 'Confirmed'):           # Status column
                
                row_to_delete = i + 1  # Google Sheets usa indici 1-based
                print(f"🔧 DEBUG - Found reservation to delete at row {row_to_delete}")
                break
        
        if row_to_delete:
            # Elimina la riga
            sheet.delete_rows(row_to_delete)
            print(f"✅ Reservation deleted from Google Sheets: phone {phone}, row {row_to_delete}")
            return True
        else:
            print(f"❌ Reservation not found for deletion: phone {phone}")
            return False
        
    except Exception as e:
        print(f"❌ Error deleting reservation from sheets: {e}")
        import traceback
        print(f"❌ TRACEBACK: {traceback.format_exc()}")
        return False

def get_user_reservations(phone_number):
    """Recupera tutte le prenotazioni attive di un utente per telefono - VERSION CON DEBUG"""
    try:
        reservations = get_reservations_from_sheets()
        print(f"🔧 DEBUG - Total reservations in sheet: {len(reservations)}")
        print(f"🔧 DEBUG - Looking for phone: '{phone_number}' (type: {type(phone_number)})")
        
        # Stampa tutte le prenotazioni per debug
        for i, reservation in enumerate(reservations):
            print(f"🔧 DEBUG - Reservation {i+1}:")
            print(f"    Name: '{reservation.get('Name', '')}' (type: {type(reservation.get('Name', ''))})")
            print(f"    Phone: '{reservation.get('Phone', '')}' (type: {type(reservation.get('Phone', ''))})")
            print(f"    Status: '{reservation.get('Status', '')}' (type: {type(reservation.get('Status', ''))})")
            print(f"    Date: '{reservation.get('Date', '')}' (type: {type(reservation.get('Date', ''))})")
            print(f"    All keys: {list(reservation.keys())}")
        
        user_reservations = []
        
        for reservation in reservations:
            phone_in_sheet = str(reservation.get('Phone', '')).strip()
            status_in_sheet = str(reservation.get('Status', '')).strip()
            phone_to_find = str(phone_number).strip()
            
            print(f"🔧 DEBUG - Comparing:")
            print(f"    Phone in sheet: '{phone_in_sheet}' == '{phone_to_find}' ? {phone_in_sheet == phone_to_find}")
            print(f"    Status in sheet: '{status_in_sheet}' == 'Confirmed' ? {status_in_sheet == 'Confirmed'}")
            
            if phone_in_sheet == phone_to_find and status_in_sheet == 'Confirmed':
                user_reservations.append(reservation)
                print(f"✅ MATCH FOUND for phone {phone_number}")
            else:
                print(f"❌ NO MATCH for phone {phone_number}")
        
        print(f"🔧 DEBUG - Found {len(user_reservations)} matching reservations")
        return user_reservations
        
    except Exception as e:
        print(f"❌ Error getting user reservations: {e}")
        import traceback
        print(f"❌ TRACEBACK: {traceback.format_exc()}")
        return []
        
def update_reservation_status(phone, date, time, new_status):
    """Aggiorna lo status di una prenotazione specifica"""
    try:
        sheet = init_google_sheets()
        if not sheet:
            return False
        
        # Ottieni tutti i dati
        all_values = sheet.get_all_values()
        
        # Trova la riga da aggiornare
        for i, row in enumerate(all_values):
            if (len(row) >= 9 and 
                row[2].strip() == str(phone).strip() and  # Phone column
                row[5].strip() == str(date).strip() and   # Date column  
                row[6].strip() == str(time).strip() and   # Time column
                row[8].strip() == 'Confirmed'):           # Status column
                
                # Aggiorna lo status (colonna 9, indice 8)
                sheet.update_cell(i + 1, 9, new_status)
                print(f"✅ Reservation status updated to '{new_status}' for {phone}")
                return True
        
        print(f"❌ Reservation not found for phone {phone}")
        return False
        
    except Exception as e:
        print(f"❌ Error updating reservation status: {e}")
        return False

def handle_modify_reservation(parameters):
    """Gestisce richiesta di modifica prenotazione"""
    try:
        print(f"🔧 DEBUG - Modify reservation parameters: {parameters}")
        
        # Estrai numero di telefono
        phone_raw = parameters.get('phone_number', parameters.get('phone', ''))
        phone = extract_value(phone_raw)
        
        print(f"🔧 DEBUG - Extracted phone: {phone}")
        
        if not phone:
            return jsonify({
                'fulfillmentText': "Please provide your phone number to find your reservation."
            })
        
        # Cerca prenotazioni dell'utente
        user_reservations = get_user_reservations(phone)
        
        if not user_reservations:
            return jsonify({
                'fulfillmentText': f"I couldn't find any active reservations for phone number {phone}. Please check the number or call us at {RESTAURANT_INFO['phone']}."
            })
        
        if len(user_reservations) == 1:
            # Una sola prenotazione - mostra dettagli
            reservation = user_reservations[0]
            
            rich_response = {
                "fulfillmentText": "Reservation found - Contact us to modify",
                "fulfillmentMessages": [
                    {
                        "text": {
                            "text": ["📋 Your current reservation:"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"👤 Name: {reservation.get('Name', '')}"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"👥 Guests: {reservation.get('Guests', '')}"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"📅 Date: {reservation.get('Date', '')}"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"🕐 Time: {reservation.get('Time', '')}"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"🪑 Table: {reservation.get('Table', '')}"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"📞 To modify this reservation, please call us at {RESTAURANT_INFO['phone']} or email {RESTAURANT_INFO['email']}"]
                        }
                    }
                ]
            }
            return jsonify(rich_response)
            
        else:
            # Multiple prenotazioni - mostra lista
            reservation_list = "📋 Your active reservations:\n\n"
            for i, reservation in enumerate(user_reservations, 1):
                reservation_list += f"{i}. {reservation.get('Date', '')} at {reservation.get('Time', '')} - {reservation.get('Guests', '')} guests\n"
            
            reservation_list += f"\n📞 To modify any reservation, please call us at {RESTAURANT_INFO['phone']} with the specific details."
            
            return jsonify({'fulfillmentText': reservation_list})
            
    except Exception as e:
        print(f"❌ Error in modify_reservation: {e}")
        return jsonify({'fulfillmentText': f'Sorry, error finding your reservation. Please call us at {RESTAURANT_INFO["phone"]}.'})

def handle_cancel_reservation(parameters):
    """Gestisce richiesta di cancellazione prenotazione - VERSIONE AGGIORNATA"""
    try:
        print(f"🔧 DEBUG - Cancel reservation parameters: {parameters}")
        
        # Estrai numero di telefono
        phone_raw = parameters.get('phone_number', parameters.get('phone', ''))
        phone = extract_value(phone_raw)
        
        print(f"🔧 DEBUG - Extracted phone: {phone}")
        
        if not phone:
            return jsonify({
                'fulfillmentText': "Please provide your phone number to find your reservation to cancel."
            })
        
        # Cerca prenotazioni dell'utente
        user_reservations = get_user_reservations(phone)
        
        if not user_reservations:
            return jsonify({
                'fulfillmentText': f"I couldn't find any active reservations for phone number {phone}. Please check the number or call us at {RESTAURANT_INFO['phone']}."
            })
        
        if len(user_reservations) == 1:
            # Una sola prenotazione - elimina completamente
            reservation = user_reservations[0]
            
            # Elimina la prenotazione dal foglio
            success = delete_reservation_from_sheets(
                phone, 
                reservation.get('Date', ''), 
                reservation.get('Time', '')
            )
            
            if success:
                rich_response = {
                    "fulfillmentText": "✅ Reservation cancelled and removed successfully!",
                    "fulfillmentMessages": [
                        {
                            "text": {
                                "text": ["✅ Reservation cancelled and removed successfully!"]
                            }
                        },
                        {
                            "text": {
                                "text": ["📋 Cancelled reservation details:"]
                            }
                        },
                        {
                            "text": {
                                "text": [f"👤 Name: {reservation.get('Name', '')}"]
                            }
                        },
                        {
                            "text": {
                                "text": [f"📅 Date: {reservation.get('Date', '')}"]
                            }
                        },
                        {
                            "text": {
                                "text": [f"🕐 Time: {reservation.get('Time', '')}"]
                            }
                        },
                        {
                            "text": {
                                "text": [f"👥 Guests: {reservation.get('Guests', '')}"]
                            }
                        },
                        {
                            "text": {
                                "text": [f"🪑 Table: {reservation.get('Table', '')} (now available again)"]
                            }
                        },
                        {
                            "text": {
                                "text": ["🗑️ Your reservation has been completely removed from our system."]
                            }
                        },
                        {
                            "text": {
                                "text": ["💔 We're sorry to see you cancel. We hope to see you again soon!"]
                            }
                        }
                    ]
                }
                return jsonify(rich_response)
            else:
                return jsonify({
                    'fulfillmentText': f"Sorry, there was an issue cancelling your reservation. Please call us at {RESTAURANT_INFO['phone']}."
                })
                
        else:
            # Multiple prenotazioni - mostra lista per scelta manuale
            reservation_list = "📋 Your active reservations:\n\n"
            for i, reservation in enumerate(user_reservations, 1):
                reservation_list += f"{i}. {reservation.get('Date', '')} at {reservation.get('Time', '')} - {reservation.get('Guests', '')} guests (Table {reservation.get('Table', '')})\n"
            
            reservation_list += f"\n📞 Please call us at {RESTAURANT_INFO['phone']} to specify which reservation you'd like to cancel."
            
            return jsonify({'fulfillmentText': reservation_list})
            
    except Exception as e:
        print(f"❌ Error in cancel_reservation: {e}")
        import traceback
        print(f"❌ TRACEBACK: {traceback.format_exc()}")
        return jsonify({'fulfillmentText': f'Sorry, error cancelling your reservation. Please call us at {RESTAURANT_INFO["phone"]}.'})

def handle_check_my_reservation(parameters):
    """Gestisce richiesta di controllo delle proprie prenotazioni - VERSION CON DEBUG"""
    try:
        print(f"🔧 DEBUG - Check my reservation parameters: {parameters}")
        
        # Estrai numero di telefono
        phone_raw = parameters.get('phone_number', parameters.get('phone', ''))
        print(f"🔧 DEBUG - phone_raw: {phone_raw} (type: {type(phone_raw)})")
        
        phone = extract_value(phone_raw)
        
        print(f"🔧 DEBUG - Extracted phone: '{phone}' (type: {type(phone)})")
        
        if not phone:
            return jsonify({
                'fulfillmentText': "To check your reservations, I need your phone number for security. Please provide the phone number you used when booking."
            })
        
        # Cerca prenotazioni dell'utente
        print(f"🔧 DEBUG - About to search for reservations...")
        user_reservations = get_user_reservations(phone)
        print(f"🔧 DEBUG - Search completed, found {len(user_reservations)} reservations")
        
        if not user_reservations:
            # Aggiungi suggerimenti per formati di telefono diversi
            phone_variants = [
                phone,
                phone.replace(' ', ''),
                phone.replace('-', ''),
                phone.replace('(', '').replace(')', ''),
                phone.replace('+', ''),
                f"+94{phone}" if not phone.startswith('+') else phone[3:],
                f"0{phone}" if not phone.startswith('0') else phone[1:],
            ]
            
            # Rimuovi duplicati mantenendo l'ordine
            phone_variants = list(dict.fromkeys(phone_variants))
            
            print(f"🔧 DEBUG - Trying phone variants: {phone_variants}")
            
            # Prova tutte le varianti
            for variant in phone_variants:
                if variant != phone:  # Evita di ricontrollare lo stesso numero
                    print(f"🔧 DEBUG - Trying variant: '{variant}'")
                    variant_reservations = get_user_reservations(variant)
                    if variant_reservations:
                        user_reservations = variant_reservations
                        print(f"🔧 DEBUG - Found reservations with variant: '{variant}'")
                        break
        
        if not user_reservations:
            return jsonify({
                'fulfillmentText': f"I couldn't find any active reservations for phone number {phone}. Please check the number format (try with/without spaces, +94 prefix, etc.) or call us at {RESTAURANT_INFO['phone']}."
            })
        
        if len(user_reservations) == 1:
            # Una sola prenotazione - mostra dettagli completi
            reservation = user_reservations[0]
            
            rich_response = {
                "fulfillmentText": "📋 Your reservation details:",
                "fulfillmentMessages": [
                    {
                        "text": {
                            "text": ["📋 Your reservation details:"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"👤 Name: {reservation.get('Name', '')}"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"📞 Phone: {reservation.get('Phone', '')}"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"📧 Email: {reservation.get('Email', '')}"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"👥 Guests: {reservation.get('Guests', '')}"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"📅 Date: {reservation.get('Date', '')}"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"🕐 Time: {reservation.get('Time', '')}"]
                        }
                    },
                    {
                        "text": {
                            "text": [f"🪑 Table: {reservation.get('Table', '')}"]
                        }
                    },
                    {
                        "text": {
                            "text": ["✅ Status: Confirmed"]
                        }
                    },
                    {
                        "text": {
                            "text": ["Need to modify or cancel? Just let me know!"]
                        }
                    }
                ]
            }
            return jsonify(rich_response)
            
        else:
            # Multiple prenotazioni - mostra lista
            rich_response = {
                "fulfillmentText": f"📋 You have {len(user_reservations)} active reservations:",
                "fulfillmentMessages": [
                    {
                        "text": {
                            "text": [f"📋 You have {len(user_reservations)} active reservations:"]
                        }
                    }
                ]
            }
            
            for i, reservation in enumerate(user_reservations, 1):
                rich_response["fulfillmentMessages"].append({
                    "text": {
                        "text": [f"{i}. {reservation.get('Date', '')} at {reservation.get('Time', '')} - {reservation.get('Guests', '')} guests (Table {reservation.get('Table', '')})"]
                    }
                })
            
            rich_response["fulfillmentMessages"].append({
                "text": {
                    "text": ["Need to modify or cancel any reservation? Just let me know!"]
                }
            })
            
            return jsonify(rich_response)
            
    except Exception as e:
        print(f"❌ Error in check_my_reservation: {e}")
        import traceback
        print(f"❌ TRACEBACK: {traceback.format_exc()}")
        return jsonify({'fulfillmentText': f'Sorry, error checking your reservations. Please call us at {RESTAURANT_INFO["phone"]}.'})

def extract_value(param):
    """Estrae valore da parametri Dialogflow con controlli robusti - VERSION CON DEBUG"""
    try:
        print(f"🔧 DEBUG - extract_value input: {param} (type: {type(param)})")
        
        if param is None or param == '':
            print(f"🔧 DEBUG - extract_value: param is None or empty")
            return None
        elif isinstance(param, list):
            # Se è una lista, prendi il primo elemento
            first_item = param[0] if param and len(param) > 0 else None
            print(f"🔧 DEBUG - extract_value: list, first_item = {first_item}")
            if isinstance(first_item, dict):
                # Se il primo elemento è un dizionario, estrai il valore
                if 'name' in first_item and first_item['name']:
                    result = str(first_item['name']).strip()
                    print(f"🔧 DEBUG - extract_value: returning from dict.name = '{result}'")
                    return result
                elif 'value' in first_item and first_item['value']:
                    result = str(first_item['value']).strip()
                    print(f"🔧 DEBUG - extract_value: returning from dict.value = '{result}'")
                    return result
                else:
                    # Prendi il primo valore non vuoto del dizionario
                    for value in first_item.values():
                        if value and str(value).strip():
                            result = str(value).strip()
                            print(f"🔧 DEBUG - extract_value: returning from dict first value = '{result}'")
                            return result
                    print(f"🔧 DEBUG - extract_value: no valid value in dict")
                    return None
            else:
                result = str(first_item).strip() if first_item not in ['', None] else None
                print(f"🔧 DEBUG - extract_value: returning from list = '{result}'")
                return result
        elif isinstance(param, dict):
            print(f"🔧 DEBUG - extract_value: dict with keys {list(param.keys())}")
            # Se è un dizionario, cerca nelle chiavi comuni
            if 'name' in param and param['name']:
                result = str(param['name']).strip()
                print(f"🔧 DEBUG - extract_value: returning from dict.name = '{result}'")
                return result
            elif 'value' in param and param['value']:
                result = str(param['value']).strip()
                print(f"🔧 DEBUG - extract_value: returning from dict.value = '{result}'")
                return result
            elif len(param) == 1:
                # Se ha una sola chiave, prendi quel valore
                value = list(param.values())[0]
                result = str(value).strip() if value not in ['', None] else None
                print(f"🔧 DEBUG - extract_value: returning single dict value = '{result}'")
                return result
            else:
                # Prendi il primo valore non vuoto
                for value in param.values():
                    if value and str(value).strip():
                        result = str(value).strip()
                        print(f"🔧 DEBUG - extract_value: returning first non-empty = '{result}'")
                        return result
                print(f"🔧 DEBUG - extract_value: no valid value in multi-key dict")
                return None
        else:
            # Se è una stringa o altro tipo
            clean_value = str(param).strip()
            result = clean_value if clean_value not in ['', 'None', 'null'] else None
            print(f"🔧 DEBUG - extract_value: returning string/other = '{result}'")
            return result
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
        elif intent_name == 'modify.reservation':
            return handle_modify_reservation(parameters)
        elif intent_name == 'cancel.reservation':
            return handle_cancel_reservation(parameters)
        elif intent_name == 'check.my.reservation':
            return handle_check_my_reservation(parameters)
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
