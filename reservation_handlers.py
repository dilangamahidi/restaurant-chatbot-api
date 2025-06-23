"""
Handlers per la gestione delle prenotazioni del ristorante - VERSIONE FIX RESPONSE
"""
from flask import jsonify
import re
import traceback

# Importa da nostri moduli
from config import RESTAURANT_INFO
from datetime_utils import (
    extract_value, 
    parse_dialogflow_datetime, 
    format_date_readable, 
    format_time_readable
)
from sheets_manager import (
    save_reservation_to_sheets,
    check_existing_reservation,
    get_user_reservations,
    update_reservation_field,
    delete_reservation_from_sheets
)
from ml_utils import (
    find_available_table,
    check_table_availability,
    get_model_status
)
from email_manager import send_confirmation_email, send_admin_notification


def handle_modify_reservation_date(parameters):
    """Gestisce modifica della data di prenotazione - FIX RESPONSE SEMPLIFICATA"""
    try:
        print(f"🔧 DEBUG - Modify date parameters: {parameters}")
        
        # Estrai parametri
        phone_raw = parameters.get('phone_number', parameters.get('phone', ''))
        phone = extract_value(phone_raw)
        new_date_raw = parameters.get('new_date', parameters.get('date', ''))
        new_date = extract_value(new_date_raw)
        
        print(f"🔧 DEBUG - Extracted: phone={phone}, new_date={new_date}")
        
        if not phone:
            response = "Please provide your phone number to find your reservation."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        if not new_date:
            response = "Please specify the new date for your reservation."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        # Cerca prenotazione esistente
        user_reservations = get_user_reservations(phone)
        
        if not user_reservations:
            response = f"I couldn't find any active reservations for phone number {phone}."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        if len(user_reservations) != 1:
            response = f"You have multiple reservations. Please call us at {RESTAURANT_INFO['phone']} to specify which one to modify."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        reservation = user_reservations[0]
        old_date = reservation.get('Date', '')
        old_time = reservation.get('Time', '')
        guests = reservation.get('Guests', 2)
        
        # Formatta la nuova data
        try:
            formatted_new_date = format_date_readable(new_date)
        except Exception as e:
            print(f"❌ Error formatting new date: {e}")
            formatted_new_date = str(new_date)
        
        # Controlla disponibilità per la nuova data (solo una volta!)
        try:
            day_of_week, hour_of_day = parse_dialogflow_datetime(new_date, old_time)
            result = find_available_table(int(guests), day_of_week, hour_of_day)
        except Exception as e:
            print(f"❌ Error checking availability: {e}")
            response = "Sorry, I'm having trouble checking availability for the new date."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        if not result['available']:
            response = f"Sorry, we don't have availability for {guests} guests on {formatted_new_date} at {old_time}. Please try a different date or time."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        # Aggiorna la data e tavolo
        new_table = result['table_number']
        
        # Aggiorna data
        date_updated = False
        try:
            date_updated = update_reservation_field(phone, old_date, old_time, 'date', formatted_new_date)
            print(f"🔧 DEBUG - date_updated result: {date_updated}")
        except Exception as e:
            print(f"❌ Error updating date: {e}")
        
        # Aggiorna tavolo
        table_updated = False
        try:
            table_updated = update_reservation_field(phone, formatted_new_date, old_time, 'table', new_table)
            print(f"🔧 DEBUG - table_updated result: {table_updated}")
        except Exception as e:
            print(f"❌ Error updating table: {e}")
        
        # SEMPRE restituisci una risposta (semplificata)
        if date_updated or table_updated:
            response = f"✅ Date updated successfully to {formatted_new_date}! Your table is now {new_table}."
            print(f"🔧 DEBUG - Returning SUCCESS: {response}")
            return jsonify({'fulfillmentText': response})
        else:
            response = f"Update completed. Please call {RESTAURANT_INFO['phone']} to verify changes."
            print(f"🔧 DEBUG - Returning FALLBACK: {response}")
            return jsonify({'fulfillmentText': response})
            
    except Exception as e:
        print(f"❌ Error in modify_reservation_date: {e}")
        response = f'Sorry, error modifying your reservation. Please call us at {RESTAURANT_INFO["phone"]}.'
        print(f"🔧 DEBUG - Returning ERROR: {response}")
        return jsonify({'fulfillmentText': response})


def handle_modify_reservation_time(parameters):
    """Gestisce modifica dell'orario di prenotazione - FIX RESPONSE SEMPLIFICATA"""
    try:
        print(f"🔧 DEBUG - Modify time parameters: {parameters}")
        
        # Estrai parametri
        phone_raw = parameters.get('phone_number', parameters.get('phone', ''))
        phone = extract_value(phone_raw)
        new_time_raw = parameters.get('new_time', parameters.get('time', ''))
        new_time = extract_value(new_time_raw)
        
        print(f"🔧 DEBUG - Extracted: phone={phone}, new_time={new_time}")
        
        if not phone:
            response = "Please provide your phone number to find your reservation."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        if not new_time:
            response = "Please specify the new time for your reservation."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        # Cerca prenotazione esistente
        user_reservations = get_user_reservations(phone)
        
        if not user_reservations:
            response = f"I couldn't find any active reservations for phone number {phone}."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        if len(user_reservations) != 1:
            response = f"You have multiple reservations. Please call us at {RESTAURANT_INFO['phone']} to specify which one to modify."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        reservation = user_reservations[0]
        old_date = reservation.get('Date', '')
        old_time = reservation.get('Time', '')
        guests = reservation.get('Guests', 2)
        
        # Formatta il nuovo orario
        try:
            formatted_new_time = format_time_readable(new_time)
        except Exception as e:
            print(f"❌ Error formatting new time: {e}")
            formatted_new_time = str(new_time)
        
        # Controlla disponibilità per il nuovo orario (solo una volta!)
        try:
            day_of_week, hour_of_day = parse_dialogflow_datetime(old_date, new_time)
            result = find_available_table(int(guests), day_of_week, hour_of_day)
        except Exception as e:
            print(f"❌ Error checking availability: {e}")
            response = "Sorry, I'm having trouble checking availability for the new time."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        if not result['available']:
            response = f"Sorry, we don't have availability for {guests} guests on {old_date} at {formatted_new_time}. Please try a different time."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        # Aggiorna l'orario e tavolo
        new_table = result['table_number']
        
        # Aggiorna orario
        time_updated = False
        try:
            time_updated = update_reservation_field(phone, old_date, old_time, 'time', formatted_new_time)
            print(f"🔧 DEBUG - time_updated result: {time_updated}")
        except Exception as e:
            print(f"❌ Error updating time: {e}")
        
        # Aggiorna tavolo
        table_updated = False
        try:
            table_updated = update_reservation_field(phone, old_date, formatted_new_time, 'table', new_table)
            print(f"🔧 DEBUG - table_updated result: {table_updated}")
        except Exception as e:
            print(f"❌ Error updating table: {e}")
        
        # SEMPRE restituisci una risposta (semplificata)
        if time_updated or table_updated:
            response = f"✅ Time updated successfully to {formatted_new_time}! Your table is now {new_table}."
            print(f"🔧 DEBUG - Returning SUCCESS: {response}")
            return jsonify({'fulfillmentText': response})
        else:
            response = f"Update completed. Please call {RESTAURANT_INFO['phone']} to verify changes."
            print(f"🔧 DEBUG - Returning FALLBACK: {response}")
            return jsonify({'fulfillmentText': response})
            
    except Exception as e:
        print(f"❌ Error in modify_reservation_time: {e}")
        response = f'Sorry, error modifying your reservation. Please call us at {RESTAURANT_INFO["phone"]}.'
        print(f"🔧 DEBUG - Returning ERROR: {response}")
        return jsonify({'fulfillmentText': response})


def handle_modify_reservation_guests(parameters):
    """Gestisce modifica del numero di ospiti - FIX RESPONSE SEMPLIFICATA"""
    try:
        print(f"🔧 DEBUG - Modify guests parameters: {parameters}")
        
        # Estrai parametri
        phone_raw = parameters.get('phone_number', parameters.get('phone', ''))
        phone = extract_value(phone_raw)
        new_guests_raw = parameters.get('new_guests', parameters.get('guests', parameters.get('number', '')))
        new_guests = extract_value(new_guests_raw)
        
        print(f"🔧 DEBUG - Extracted: phone={phone}, new_guests={new_guests}")
        
        if not phone:
            response = "Please provide your phone number to find your reservation."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        if not new_guests:
            response = "Please specify the new number of guests for your reservation."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        # Converti numero ospiti
        try:
            clean_guests = str(new_guests).strip().replace('guests', '').replace('people', '').replace('persons', '').strip()
            
            word_to_num = {
                'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
                'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
                'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
                'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20
            }
            
            if clean_guests.lower() in word_to_num:
                guest_count = word_to_num[clean_guests.lower()]
            else:
                guest_count = int(float(clean_guests))
            
            if guest_count < 1 or guest_count > 20:
                response = "I can accommodate between 1 and 20 guests. Please specify a valid number."
                print(f"🔧 DEBUG - Returning: {response}")
                return jsonify({'fulfillmentText': response})
                
            print(f"🔧 DEBUG - Final guest_count: {guest_count}")
            
        except (ValueError, TypeError) as e:
            print(f"❌ Error converting guests '{new_guests}': {e}")
            response = f"Please provide a valid number of guests (you entered: '{new_guests}')."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        # Cerca prenotazione esistente
        user_reservations = get_user_reservations(phone)
        
        if not user_reservations:
            response = f"I couldn't find any active reservations for phone number {phone}."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        if len(user_reservations) != 1:
            response = f"You have multiple reservations. Please call us at {RESTAURANT_INFO['phone']} to specify which one to modify."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        reservation = user_reservations[0]
        old_date = reservation.get('Date', '')
        old_time = reservation.get('Time', '')
        old_guests = reservation.get('Guests', 2)
        
        print(f"🔧 DEBUG - Found reservation: date={old_date}, time={old_time}, old_guests={old_guests}, new_guests={guest_count}")
        
        # Controlla disponibilità per il nuovo numero di ospiti (solo una volta!)
        try:
            day_of_week, hour_of_day = parse_dialogflow_datetime(old_date, old_time)
            result = find_available_table(guest_count, day_of_week, hour_of_day)
        except Exception as e:
            print(f"❌ Error checking availability: {e}")
            response = f"Sorry, I'm having trouble checking availability for {guest_count} guests."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        if not result['available']:
            response = f"Sorry, we don't have availability for {guest_count} guests on {old_date} at {old_time}. Please try a different time or date."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        # Aggiorna il numero di ospiti e tavolo
        new_table = result['table_number']
        
        # Aggiorna numero ospiti
        guests_updated = False
        try:
            guests_updated = update_reservation_field(phone, old_date, old_time, 'guests', guest_count)
            print(f"🔧 DEBUG - guests_updated result: {guests_updated}")
        except Exception as e:
            print(f"❌ Error updating guests: {e}")
        
        # Aggiorna tavolo
        table_updated = False
        try:
            table_updated = update_reservation_field(phone, old_date, old_time, 'table', new_table)
            print(f"🔧 DEBUG - table_updated result: {table_updated}")
        except Exception as e:
            print(f"❌ Error updating table: {e}")
        
        # SEMPRE restituisci una risposta (semplificata)
        if guests_updated or table_updated:
            response = f"✅ Guest count updated successfully to {guest_count} guests (was {old_guests})! Your table is now {new_table}."
            print(f"🔧 DEBUG - Returning SUCCESS: {response}")
            return jsonify({'fulfillmentText': response})
        else:
            response = f"Update completed. Please call {RESTAURANT_INFO['phone']} to verify changes."
            print(f"🔧 DEBUG - Returning FALLBACK: {response}")
            return jsonify({'fulfillmentText': response})
            
    except Exception as e:
        print(f"❌ Error in modify_reservation_guests: {e}")
        response = f'Sorry, error modifying your reservation. Please call us at {RESTAURANT_INFO["phone"]}.'
        print(f"🔧 DEBUG - Returning ERROR: {response}")
        return jsonify({'fulfillmentText': response})


def handle_modify_reservation(parameters):
    """Gestisce richiesta di modifica prenotazione - VERSIONE SEMPLIFICATA"""
    try:
        print(f"🔧 DEBUG - Modify reservation parameters: {parameters}")
        
        # Estrai numero di telefono
        phone_raw = parameters.get('phone_number', parameters.get('phone', ''))
        phone = extract_value(phone_raw)
        
        print(f"🔧 DEBUG - Extracted phone: {phone}")
        
        if not phone:
            response = "Please provide your phone number to find your reservation."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        # Cerca prenotazioni dell'utente
        user_reservations = get_user_reservations(phone)
        
        if not user_reservations:
            response = f"I couldn't find any active reservations for phone number {phone}. Please check the number or call us at {RESTAURANT_INFO['phone']}."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        if len(user_reservations) == 1:
            # Una sola prenotazione - mostra opzioni di modifica (semplificata)
            reservation = user_reservations[0]
            response = f"📋 Your current reservation: {reservation.get('Name', '')} for {reservation.get('Guests', '')} guests on {reservation.get('Date', '')} at {reservation.get('Time', '')} (Table {reservation.get('Table', '')}). What would you like to modify? You can say: 'Change the date to tomorrow', 'Change the time to 8pm' or 'Change to 4 guests'."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        else:
            # Multiple prenotazioni
            response = f"You have {len(user_reservations)} reservations. Please call us at {RESTAURANT_INFO['phone']} to specify which one to modify."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
            
    except Exception as e:
        print(f"❌ Error in modify_reservation: {e}")
        response = f'Sorry, error finding your reservation. Please call us at {RESTAURANT_INFO["phone"]}.'
        print(f"🔧 DEBUG - Returning ERROR: {response}")
        return jsonify({'fulfillmentText': response})


def handle_cancel_reservation(parameters):
    """Gestisce richiesta di cancellazione prenotazione - VERSIONE SEMPLIFICATA"""
    try:
        print(f"🔧 DEBUG - Cancel reservation parameters: {parameters}")
        
        # Estrai numero di telefono
        phone_raw = parameters.get('phone_number', parameters.get('phone', ''))
        phone = extract_value(phone_raw)
        
        print(f"🔧 DEBUG - Extracted phone: {phone}")
        
        if not phone:
            response = "Please provide your phone number to find your reservation to cancel."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        # Cerca prenotazioni dell'utente
        user_reservations = get_user_reservations(phone)
        
        if not user_reservations:
            response = f"I couldn't find any active reservations for phone number {phone}. Please check the number or call us at {RESTAURANT_INFO['phone']}."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
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
                response = f"✅ Reservation cancelled successfully! Your reservation for {reservation.get('Name', '')} on {reservation.get('Date', '')} at {reservation.get('Time', '')} for {reservation.get('Guests', '')} guests (Table {reservation.get('Table', '')}) has been removed. We're sorry to see you cancel. We hope to see you again soon!"
                print(f"🔧 DEBUG - Returning SUCCESS: {response}")
                return jsonify({'fulfillmentText': response})
            else:
                response = f"Sorry, there was an issue cancelling your reservation. Please call us at {RESTAURANT_INFO['phone']}."
                print(f"🔧 DEBUG - Returning FALLBACK: {response}")
                return jsonify({'fulfillmentText': response})
        else:
            # Multiple prenotazioni
            response = f"You have {len(user_reservations)} reservations. Please call us at {RESTAURANT_INFO['phone']} to specify which one to cancel."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
            
    except Exception as e:
        print(f"❌ Error in cancel_reservation: {e}")
        response = f'Sorry, error cancelling your reservation. Please call us at {RESTAURANT_INFO["phone"]}.'
        print(f"🔧 DEBUG - Returning ERROR: {response}")
        return jsonify({'fulfillmentText': response})


def handle_check_my_reservation(parameters):
    """Gestisce richiesta di controllo delle proprie prenotazioni - VERSIONE SEMPLIFICATA"""
    try:
        print(f"🔧 DEBUG - Check my reservation parameters: {parameters}")
        
        # Estrai numero di telefono
        phone_raw = parameters.get('phone_number', parameters.get('phone', ''))
        phone = extract_value(phone_raw)
        
        print(f"🔧 DEBUG - Extracted phone: {phone}")
        
        if not phone:
            response = "To check your reservations, I need your phone number for security. Please provide the phone number you used when booking."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        # Cerca prenotazioni dell'utente
        user_reservations = get_user_reservations(phone)
        
        if not user_reservations:
            response = f"I couldn't find any active reservations for phone number {phone}. Please check the number format or call us at {RESTAURANT_INFO['phone']}."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        if len(user_reservations) == 1:
            # Una sola prenotazione - mostra dettagli (semplificata)
            reservation = user_reservations[0]
            response = f"📋 Your reservation: {reservation.get('Name', '')} ({reservation.get('Phone', '')}) - {reservation.get('Guests', '')} guests on {reservation.get('Date', '')} at {reservation.get('Time', '')} - Table {reservation.get('Table', '')} - Status: Confirmed. Need to modify or cancel? Just let me know!"
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        else:
            # Multiple prenotazioni
            reservation_details = []
            for i, res in enumerate(user_reservations, 1):
                reservation_details.append(f"{i}. {res.get('Date', '')} at {res.get('Time', '')} - {res.get('Guests', '')} guests (Table {res.get('Table', '')})")
            
            response = f"📋 You have {len(user_reservations)} active reservations: " + "; ".join(reservation_details) + ". Need to modify or cancel any reservation? Just let me know!"
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
            
    except Exception as e:
        print(f"❌ Error in check_my_reservation: {e}")
        response = f'Sorry, error checking your reservations. Please call us at {RESTAURANT_INFO["phone"]}.'
        print(f"🔧 DEBUG - Returning ERROR: {response}")
        return jsonify({'fulfillmentText': response})


def handle_check_table_specific(parameters):
    """Gestisce controllo tavolo specifico - VERSIONE SEMPLIFICATA"""
    try:
        print(f"🔧 DEBUG - Check table parameters: {parameters}")
        
        # Estrai parametri
        table_raw = parameters.get('table_number', parameters.get('number', parameters.get('table', '')))
        date_raw = parameters.get('date', parameters.get('day_of_week', ''))
        time_raw = parameters.get('time', parameters.get('hour_of_day', ''))
        
        table_number = extract_value(table_raw)
        date = extract_value(date_raw)
        time = extract_value(time_raw)
        
        print(f"🔧 DEBUG - Extracted: table={table_number}, date={date}, time={time}")
        
        # Converti numero tavolo
        try:
            if not table_number:
                response = "Please specify which table number you'd like to check (1-20)."
                print(f"🔧 DEBUG - Returning: {response}")
                return jsonify({'fulfillmentText': response})
            
            table_str = str(table_number).strip().lower().replace('table', '').replace('number', '').replace('#', '').strip()
            table_num = int(float(table_str))
            
            if table_num < 1 or table_num > 20:
                response = "Please specify a table number between 1 and 20."
                print(f"🔧 DEBUG - Returning: {response}")
                return jsonify({'fulfillmentText': response})
                
        except (ValueError, TypeError) as e:
            print(f"❌ Error converting table '{table_number}': {e}")
            response = "Please provide a valid table number (1-20)."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        # Controlla parametri mancanti
        if not date or not time:
            response = f"I need the date and time to check table {table_num} availability."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        # Converti date/time per ML
        try:
            day_of_week, hour_of_day = parse_dialogflow_datetime(date, time)
            is_available = check_table_availability(table_num, 4, day_of_week, hour_of_day)  # Default 4 guests
            
            # Formatta data e ora
            formatted_date = format_date_readable(date)
            formatted_time = format_time_readable(time)
            
            if is_available:
                response = f"✅ Good news! Table {table_num} is available on {formatted_date} at {formatted_time}!"
            else:
                response = f"😔 Sorry, table {table_num} is already reserved on {formatted_date} at {formatted_time}."
                
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
            
        except Exception as e:
            print(f"❌ Error checking availability: {e}")
            response = 'Sorry, error checking table availability. Please call us.'
            print(f"🔧 DEBUG - Returning ERROR: {response}")
            return jsonify({'fulfillmentText': response})
            
    except Exception as e:
        print(f"❌ Error in check_table_specific: {e}")
        response = 'Sorry, error checking table availability. Please call us.'
        print(f"🔧 DEBUG - Returning ERROR: {response}")
        return jsonify({'fulfillmentText': response})


def handle_make_reservation(parameters):
    """Gestisce prenotazione completa - VERSIONE SEMPLIFICATA SENZA TIMEOUT"""
    try:
        print(f"🔧 DEBUG - Make reservation parameters: {parameters}")
        
        # Estrai parametri con controlli robusti
        name = extract_value(parameters.get('name', parameters.get('person', '')))
        phone = extract_value(parameters.get('phone_number', parameters.get('phone', '')))
        email = extract_value(parameters.get('email', ''))
        guests = extract_value(parameters.get('guest_count', parameters.get('guests', parameters.get('number', 2))))
        date = extract_value(parameters.get('day_of_week', parameters.get('date', '')))
        time = extract_value(parameters.get('hour_of_day', parameters.get('time', '')))
        
        print(f"🔧 DEBUG - Extracted: name={name}, phone={phone}, email={email}, guests={guests}, date={date}, time={time}")
        
        # Converti numero ospiti
        try:
            guest_str = str(guests).strip().lower().replace('guests', '').replace('people', '').strip()
            guest_count = int(float(guest_str)) if guest_str else 2
            
            if guest_count < 1 or guest_count > 20:
                response = f"I can accommodate between 1 and 20 guests. You requested {guest_count} guests."
                print(f"🔧 DEBUG - Returning: {response}")
                return jsonify({'fulfillmentText': response})
                
        except (ValueError, TypeError):
            guest_count = 2  # Default fallback
        
        # Valida parametri essenziali
        if not name or len(str(name).strip()) < 2:
            response = "I need your full name to complete the reservation."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        if not phone:
            response = "I need your phone number to complete the reservation."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        if not email or '@' not in str(email):
            response = "I need a valid email address to complete the reservation."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        if not date or not time:
            response = "I need both the date and time for your reservation."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
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
                response = f"⚠️ You already have a reservation for {formatted_date} at {formatted_time}."
                print(f"🔧 DEBUG - Returning: {response}")
                return jsonify({'fulfillmentText': response})
        except Exception as e:
            print(f"❌ Error checking duplicates: {e}")
        
        # Controlla disponibilità (con fallback se ML non funziona)
        try:
            day_of_week, hour_of_day = parse_dialogflow_datetime(date, time)
            result = find_available_table(guest_count, day_of_week, hour_of_day)
            
            if not result['available']:
                response = f"😔 Sorry, we don't have availability for {guest_count} guests on {formatted_date} at {formatted_time}. Please try a different time."
                print(f"🔧 DEBUG - Returning: {response}")
                return jsonify({'fulfillmentText': response})
                
        except Exception as e:
            print(f"❌ Error checking availability: {e}")
            # Fallback: assegna tavolo 1 e procedi
            result = {'available': True, 'table_number': 1}
        
        # Salva prenotazione
        table_num = result['table_number']
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
        
        # RISPOSTA IMMEDIATA (sempre semplificata)
        if sheets_saved:
            response = f"🎉 Reservation confirmed for {name}! {guest_count} guests on {formatted_date} at {formatted_time}, Table {table_num}. Confirmation email will be sent shortly!"
        else:
            response = f"✅ Reservation received for {name}! {guest_count} guests on {formatted_date} at {formatted_time}. Our staff will contact you to confirm details."
        
        print(f"🔧 DEBUG - Returning SUCCESS: {response}")
        
        # Email in background (non blocca la risposta)
        try:
            import threading
            def send_emails_background():
                try:
                    send_confirmation_email(reservation_data)
                    send_admin_notification(reservation_data)
                    print("📧 Background emails sent")
                except:
                    print("❌ Background email failed")
            
            email_thread = threading.Thread(target=send_emails_background)
            email_thread.daemon = True
            email_thread.start()
        except:
            pass  # Non importa se l'email fallisce
        
        return jsonify({'fulfillmentText': response})
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR in make_reservation: {e}")
        response = f"I'm sorry, there was a technical issue. Please call us directly at {RESTAURANT_INFO['phone']} and we'll be happy to help you."
        print(f"🔧 DEBUG - Returning CRITICAL ERROR: {response}")
        return jsonify({'fulfillmentText': response})
