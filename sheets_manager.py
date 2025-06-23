"""
Gestione Google Sheets per le prenotazioni
"""
import os
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from config import SCOPES, SHEET_ID


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


def update_reservation_field(phone, old_date, old_time, field, new_value):
    """Aggiorna un campo specifico di una prenotazione"""
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
                row[5].strip() == str(old_date).strip() and   # Date column  
                row[6].strip() == str(old_time).strip() and   # Time column
                row[8].strip() == 'Confirmed'):           # Status column
                
                # Mappa dei campi alle colonne (1-based per Google Sheets)
                field_to_column = {
                    'date': 6,    # Column F
                    'time': 7,    # Column G  
                    'guests': 5,  # Column E
                    'table': 8    # Column H
                }
                
                if field in field_to_column:
                    column_num = field_to_column[field]
                    sheet.update_cell(i + 1, column_num, new_value)
                    print(f"✅ Updated {field} to '{new_value}' for reservation {phone}")
                    return True
        
        print(f"❌ Reservation not found for update: phone {phone}")
        return False
        
    except Exception as e:
        print(f"❌ Error updating reservation field: {e}")
        import traceback
        print(f"❌ TRACEBACK: {traceback.format_exc()}")
        return False


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
