"""
Google Sheets management for restaurant reservations
"""
import os
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from config import SCOPES, SHEET_ID


def init_google_sheets():
    """Initialize Google Sheets connection"""
    try:
        # First try environment variables (for production deployment)
        google_credentials = os.environ.get('GOOGLE_CREDENTIALS')
        
        if google_credentials:
            print("🔧 DEBUG - Found credentials in environment variable")
            # Production: use environment variable containing service account JSON
            creds_dict = json.loads(google_credentials)
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        else:
            print("🔧 DEBUG - Looking for local credentials.json file")
            # Local development: use credentials file
            if os.path.exists('credentials.json'):
                print("🔧 DEBUG - credentials.json file found")
                creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
            else:
                print("❌ No credentials found - Google Sheets disabled")
                return None
        
        print("🔧 DEBUG - Attempting to connect to Google Sheets...")
        # Authorize the client and open the spreadsheet
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID).sheet1
        print("✅ Google Sheets connected successfully!")
        return sheet
        
    except Exception as e:
        print(f"❌ Google Sheets error: {e}")
        print(f"🔧 DEBUG - Error type: {type(e)}")
        return None


def save_reservation_to_sheets(reservation_data, language_code='en'):
    """Save reservation data to Google Sheets with multilingual support"""
    try:
        # Initialize connection to Google Sheets
        sheet = init_google_sheets()
        if not sheet:
            print("❌ Unable to connect to Google Sheets")
            return False
        
        # Prepare data for the spreadsheet row
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        row_data = [
            timestamp,                      # Column A: Timestamp
            reservation_data['name'],       # Column B: Customer name
            reservation_data['phone'],      # Column C: Phone number
            reservation_data['email'],      # Column D: Email address
            reservation_data['guests'],     # Column E: Number of guests
            reservation_data['date'],       # Column F: Reservation date
            reservation_data['time'],       # Column G: Reservation time
            reservation_data['table'],      # Column H: Table assignment
            'Confirmed'                     # Column I: Status
        ]
        
        # Append the new row to the spreadsheet
        sheet.append_row(row_data)
        print(f"✅ Reservation saved to Google Sheets: {reservation_data['name']}")
        return True
        
    except Exception as e:
        print(f"❌ Error saving to Google Sheets: {e}")
        return False


def get_reservations_from_sheets():
    """Retrieve all reservations from the spreadsheet"""
    try:
        # Initialize connection to Google Sheets
        sheet = init_google_sheets()
        if not sheet:
            return []
        
        # Get all records (skipping the header row)
        records = sheet.get_all_records()
        return records
        
    except Exception as e:
        print(f"❌ Error reading from Google Sheets: {e}")
        return []


def check_existing_reservation(name, phone, date, time):
    """Check if an identical reservation already exists"""
    try:
        # Get all existing reservations
        reservations = get_reservations_from_sheets()
        
        # Check for duplicate reservations
        for reservation in reservations:
            if (reservation.get('Name', '').lower() == name.lower() and
                reservation.get('Phone', '') == phone and
                reservation.get('Date', '') == date and
                reservation.get('Time', '') == time and
                reservation.get('Status', '') == 'Confirmed'):
                return True
        return False
        
    except Exception as e:
        print(f"❌ Error checking for duplicates: {e}")
        return False


def get_user_reservations(phone_number, language_code='en'):
    """Retrieve all active reservations for a user by phone number with multilingual support"""
    try:
        # Get all reservations from the spreadsheet
        reservations = get_reservations_from_sheets()
        print(f"🔧 DEBUG - Total reservations in sheet: {len(reservations)}")
        print(f"🔧 DEBUG - Looking for phone: '{phone_number}' (type: {type(phone_number)})")
        
        # Debug: print all reservations for troubleshooting
        for i, reservation in enumerate(reservations):
            print(f"🔧 DEBUG - Reservation {i+1}:")
            print(f"    Name: '{reservation.get('Name', '')}' (type: {type(reservation.get('Name', ''))})")
            print(f"    Phone: '{reservation.get('Phone', '')}' (type: {type(reservation.get('Phone', ''))})")
            print(f"    Status: '{reservation.get('Status', '')}' (type: {type(reservation.get('Status', ''))})")
            print(f"    Date: '{reservation.get('Date', '')}' (type: {type(reservation.get('Date', ''))})")
            print(f"    All keys: {list(reservation.keys())}")
        
        # Filter reservations for the specific user
        user_reservations = []
        
        for reservation in reservations:
            # Convert to string and strip whitespace for comparison
            phone_in_sheet = str(reservation.get('Phone', '')).strip()
            status_in_sheet = str(reservation.get('Status', '')).strip()
            phone_to_find = str(phone_number).strip()
            
            print(f"🔧 DEBUG - Comparing:")
            print(f"    Phone in sheet: '{phone_in_sheet}' == '{phone_to_find}' ? {phone_in_sheet == phone_to_find}")
            print(f"    Status in sheet: '{status_in_sheet}' == 'Confirmed' ? {status_in_sheet == 'Confirmed'}")
            
            # Match phone number and confirmed status
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


def update_reservation_field(phone, old_date, old_time, field, new_value, language_code='en'):
    """Update a specific field of a reservation with multilingual support"""
    try:
        # Initialize connection to Google Sheets
        sheet = init_google_sheets()
        if not sheet:
            return False
        
        # Get all spreadsheet data
        all_values = sheet.get_all_values()
        
        # Find the row to update by matching phone, date, time, and status
        for i, row in enumerate(all_values):
            if (len(row) >= 9 and 
                row[2].strip() == str(phone).strip() and  # Phone column (C)
                row[5].strip() == str(old_date).strip() and   # Date column (F)
                row[6].strip() == str(old_time).strip() and   # Time column (G)
                row[8].strip() == 'Confirmed'):           # Status column (I)
                
                # Map field names to column numbers (1-based for Google Sheets API)
                field_to_column = {
                    'date': 6,    # Column F
                    'time': 7,    # Column G  
                    'guests': 5,  # Column E
                    'table': 8    # Column H
                }
                
                # Update the specific field if it exists in the mapping
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


def delete_reservation_from_sheets(phone, date, time, language_code='en'):
    """Completely delete a reservation from Google Sheets with multilingual support"""
    try:
        # Initialize connection to Google Sheets
        sheet = init_google_sheets()
        if not sheet:
            return False
        
        # Get all spreadsheet data
        all_values = sheet.get_all_values()
        
        # Find the row to delete by matching phone, date, time, and status
        row_to_delete = None
        for i, row in enumerate(all_values):
            if (len(row) >= 9 and 
                row[2].strip() == str(phone).strip() and  # Phone column (C)
                row[5].strip() == str(date).strip() and   # Date column (F)
                row[6].strip() == str(time).strip() and   # Time column (G)
                row[8].strip() == 'Confirmed'):           # Status column (I)
                
                row_to_delete = i + 1  # Google Sheets uses 1-based indexing
                print(f"🔧 DEBUG - Found reservation to delete at row {row_to_delete}")
                break
        
        if row_to_delete:
            # Delete the entire row
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


def update_reservation_status(phone, date, time, new_status, language_code='en'):
    """Update the status of a specific reservation with multilingual support"""
    try:
        # Initialize connection to Google Sheets
        sheet = init_google_sheets()
        if not sheet:
            return False
        
        # Get all spreadsheet data
        all_values = sheet.get_all_values()
        
        # Find the row to update by matching phone, date, time, and current status
        for i, row in enumerate(all_values):
            if (len(row) >= 9 and 
                row[2].strip() == str(phone).strip() and  # Phone column (C)
                row[5].strip() == str(date).strip() and   # Date column (F)
                row[6].strip() == str(time).strip() and   # Time column (G)
                row[8].strip() == 'Confirmed'):           # Status column (I)
                
                # Update the status (column 9, index 8 in 0-based, but API uses 1-based)
                sheet.update_cell(i + 1, 9, new_status)
                print(f"✅ Reservation status updated to '{new_status}' for {phone}")
                return True
        
        print(f"❌ Reservation not found for phone {phone}")
        return False
        
    except Exception as e:
        print(f"❌ Error updating reservation status: {e}")
        return False
