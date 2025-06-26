"""
Google Sheets management for reservations
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
        print("🔧 DEBUG - Starting Google Sheets initialization process...")
        
        # First try environment variables (for production)
        google_credentials = os.environ.get('GOOGLE_CREDENTIALS')
        
        if google_credentials:
            print("🔧 DEBUG - Found credentials in environment variable")
            print("🔧 DEBUG - Parsing JSON credentials from environment...")
            # In production: use environment variable
            creds_dict = json.loads(google_credentials)
            print("🔧 DEBUG - Creating credentials from service account info...")
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        else:
            print("🔧 DEBUG - Looking for local credentials.json file")
            # In local development: use file
            if os.path.exists('credentials.json'):
                print("🔧 DEBUG - credentials.json file found locally")
                print("🔧 DEBUG - Loading credentials from file...")
                creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
            else:
                print("❌ No credentials found - Google Sheets disabled")
                return None
        
        print("🔧 DEBUG - Attempting connection to Google Sheets API...")
        print("🔧 DEBUG - Authorizing client with credentials...")
        client = gspread.authorize(creds)
        print("🔧 DEBUG - Opening spreadsheet by ID:", SHEET_ID)
        sheet = client.open_by_key(SHEET_ID).sheet1
        print("✅ Google Sheets connected successfully!")
        print("🔧 DEBUG - Using worksheet:", sheet.title)
        return sheet
        
    except Exception as e:
        print(f"❌ Google Sheets error: {e}")
        print(f"🔧 DEBUG - Error type: {type(e)}")
        print("🔧 DEBUG - Connection failed, returning None")
        return None


def save_reservation_to_sheets(reservation_data):
    """Save reservation to Google Sheets"""
    try:
        print("🔧 DEBUG - Starting reservation save process...")
        print(f"🔧 DEBUG - Reservation data: {reservation_data}")
        
        sheet = init_google_sheets()
        if not sheet:
            print("❌ Unable to connect to Google Sheets")
            return False
        
        print("🔧 DEBUG - Preparing data for sheet insertion...")
        # Prepare data for the sheet
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"🔧 DEBUG - Generated timestamp: {timestamp}")
        
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
        
        print(f"🔧 DEBUG - Row data to insert: {row_data}")
        print("🔧 DEBUG - Appending row to Google Sheet...")
        
        # Add row to sheet
        sheet.append_row(row_data)
        print(f"✅ Reservation saved to Google Sheets: {reservation_data['name']}")
        print("🔧 DEBUG - Save operation completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error saving to Google Sheets: {e}")
        print(f"🔧 DEBUG - Save operation failed with error type: {type(e)}")
        return False


def get_reservations_from_sheets():
    """Retrieve all reservations from the sheet"""
    try:
        print("🔧 DEBUG - Starting reservations retrieval process...")
        
        sheet = init_google_sheets()
        if not sheet:
            print("🔧 DEBUG - Sheet connection failed, returning empty list")
            return []
        
        print("🔧 DEBUG - Fetching all records from sheet (skipping header)...")
        # Get all records (skipping header)
        records = sheet.get_all_records()
        print(f"🔧 DEBUG - Retrieved {len(records)} records from sheet")
        print("🔧 DEBUG - Records retrieval completed successfully")
        return records
        
    except Exception as e:
        print(f"❌ Error reading from Google Sheets: {e}")
        print(f"🔧 DEBUG - Retrieval failed with error type: {type(e)}")
        return []


def check_existing_reservation(name, phone, date, time):
    """Check if an identical reservation already exists"""
    try:
        print("🔧 DEBUG - Starting duplicate reservation check...")
        print(f"🔧 DEBUG - Checking for: name={name}, phone={phone}, date={date}, time={time}")
        
        reservations = get_reservations_from_sheets()
        print(f"🔧 DEBUG - Got {len(reservations)} reservations to check against")
        
        for i, reservation in enumerate(reservations):
            print(f"🔧 DEBUG - Checking reservation {i+1}/{len(reservations)}")
            
            if (reservation.get('Name', '').lower() == name.lower() and
                reservation.get('Phone', '') == phone and
                reservation.get('Date', '') == date and
                reservation.get('Time', '') == time and
                reservation.get('Status', '') == 'Confirmed'):
                
                print("🔧 DEBUG - Found matching reservation - duplicate detected!")
                return True
        
        print("🔧 DEBUG - No duplicate reservation found")
        return False
        
    except Exception as e:
        print(f"❌ Error checking duplicates: {e}")
        print(f"🔧 DEBUG - Duplicate check failed with error type: {type(e)}")
        return False


def get_user_reservations(phone_number):
    """Retrieve all active reservations for a user by phone - VERSION WITH DEBUG"""
    try:
        print("🔧 DEBUG - Starting user reservations lookup...")
        print(f"🔧 DEBUG - Searching for phone number: '{phone_number}' (type: {type(phone_number)})")
        
        reservations = get_reservations_from_sheets()
        print(f"🔧 DEBUG - Total reservations in sheet: {len(reservations)}")
        print(f"🔧 DEBUG - Looking for phone: '{phone_number}' (type: {type(phone_number)})")
        
        # Print all reservations for debug
        print("🔧 DEBUG - Examining all reservations in detail:")
        for i, reservation in enumerate(reservations):
            print(f"🔧 DEBUG - Reservation {i+1}:")
            print(f"    Name: '{reservation.get('Name', '')}' (type: {type(reservation.get('Name', ''))})")
            print(f"    Phone: '{reservation.get('Phone', '')}' (type: {type(reservation.get('Phone', ''))})")
            print(f"    Status: '{reservation.get('Status', '')}' (type: {type(reservation.get('Status', ''))})")
            print(f"    Date: '{reservation.get('Date', '')}' (type: {type(reservation.get('Date', ''))})")
            print(f"    All keys: {list(reservation.keys())}")
        
        user_reservations = []
        print("🔧 DEBUG - Starting phone number matching process...")
        
        for reservation in reservations:
            phone_in_sheet = str(reservation.get('Phone', '')).strip()
            status_in_sheet = str(reservation.get('Status', '')).strip()
            phone_to_find = str(phone_number).strip()
            
            print(f"🔧 DEBUG - Comparing reservation:")
            print(f"    Phone in sheet: '{phone_in_sheet}' == '{phone_to_find}' ? {phone_in_sheet == phone_to_find}")
            print(f"    Status in sheet: '{status_in_sheet}' == 'Confirmed' ? {status_in_sheet == 'Confirmed'}")
            
            if phone_in_sheet == phone_to_find and status_in_sheet == 'Confirmed':
                user_reservations.append(reservation)
                print(f"✅ MATCH FOUND for phone {phone_number}")
            else:
                print(f"❌ NO MATCH for phone {phone_number}")
        
        print(f"🔧 DEBUG - Found {len(user_reservations)} matching reservations")
        print("🔧 DEBUG - User reservations lookup completed")
        return user_reservations
        
    except Exception as e:
        print(f"❌ Error getting user reservations: {e}")
        print(f"🔧 DEBUG - User lookup failed with error type: {type(e)}")
        import traceback
        print(f"❌ TRACEBACK: {traceback.format_exc()}")
        return []


def update_reservation_field(phone, old_date, old_time, field, new_value):
    """Update a specific field of a reservation"""
    try:
        print("🔧 DEBUG - Starting reservation field update...")
        print(f"🔧 DEBUG - Update parameters: phone={phone}, date={old_date}, time={old_time}")
        print(f"🔧 DEBUG - Field to update: {field} -> {new_value}")
        
        sheet = init_google_sheets()
        if not sheet:
            print("🔧 DEBUG - Sheet connection failed")
            return False
        
        print("🔧 DEBUG - Fetching all sheet values for update search...")
        # Get all data
        all_values = sheet.get_all_values()
        print(f"🔧 DEBUG - Retrieved {len(all_values)} rows from sheet")
        
        # Find the row to update
        print("🔧 DEBUG - Searching for matching reservation to update...")
        for i, row in enumerate(all_values):
            print(f"🔧 DEBUG - Checking row {i+1}: {row[:9] if len(row) >= 9 else row}")
            
            if (len(row) >= 9 and 
                row[2].strip() == str(phone).strip() and  # Phone column
                row[5].strip() == str(old_date).strip() and   # Date column  
                row[6].strip() == str(old_time).strip() and   # Time column
                row[8].strip() == 'Confirmed'):           # Status column
                
                print(f"🔧 DEBUG - Found matching reservation at row {i+1}")
                
                # Map fields to columns (1-based for Google Sheets)
                field_to_column = {
                    'date': 6,    # Column F
                    'time': 7,    # Column G  
                    'guests': 5,  # Column E
                    'table': 8    # Column H
                }
                
                if field in field_to_column:
                    column_num = field_to_column[field]
                    print(f"🔧 DEBUG - Updating cell at row {i+1}, column {column_num}")
                    sheet.update_cell(i + 1, column_num, new_value)
                    print(f"✅ Updated {field} to '{new_value}' for reservation {phone}")
                    print("🔧 DEBUG - Field update completed successfully")
                    return True
        
        print(f"❌ Reservation not found for update: phone {phone}")
        print("🔧 DEBUG - No matching reservation found for update")
        return False
        
    except Exception as e:
        print(f"❌ Error updating reservation field: {e}")
        print(f"🔧 DEBUG - Update failed with error type: {type(e)}")
        import traceback
        print(f"❌ TRACEBACK: {traceback.format_exc()}")
        return False


def delete_reservation_from_sheets(phone, date, time):
    """Completely delete a reservation from Google Sheets"""
    try:
        print("🔧 DEBUG - Starting reservation deletion process...")
        print(f"🔧 DEBUG - Deletion parameters: phone={phone}, date={date}, time={time}")
        
        sheet = init_google_sheets()
        if not sheet:
            print("🔧 DEBUG - Sheet connection failed")
            return False
        
        print("🔧 DEBUG - Fetching all sheet values for deletion search...")
        # Get all data
        all_values = sheet.get_all_values()
        print(f"🔧 DEBUG - Retrieved {len(all_values)} rows from sheet")
        
        # Find the row to delete
        row_to_delete = None
        print("🔧 DEBUG - Searching for matching reservation to delete...")
        
        for i, row in enumerate(all_values):
            print(f"🔧 DEBUG - Checking row {i+1} for deletion match...")
            
            if (len(row) >= 9 and 
                row[2].strip() == str(phone).strip() and  # Phone column
                row[5].strip() == str(date).strip() and   # Date column  
                row[6].strip() == str(time).strip() and   # Time column
                row[8].strip() == 'Confirmed'):           # Status column
                
                row_to_delete = i + 1  # Google Sheets uses 1-based indices
                print(f"🔧 DEBUG - Found reservation to delete at row {row_to_delete}")
                break
        
        if row_to_delete:
            print(f"🔧 DEBUG - Deleting row {row_to_delete} from sheet...")
            # Delete the row
            sheet.delete_rows(row_to_delete)
            print(f"✅ Reservation deleted from Google Sheets: phone {phone}, row {row_to_delete}")
            print("🔧 DEBUG - Deletion completed successfully")
            return True
        else:
            print(f"❌ Reservation not found for deletion: phone {phone}")
            print("🔧 DEBUG - No matching reservation found for deletion")
            return False
        
    except Exception as e:
        print(f"❌ Error deleting reservation from sheets: {e}")
        print(f"🔧 DEBUG - Deletion failed with error type: {type(e)}")
        import traceback
        print(f"❌ TRACEBACK: {traceback.format_exc()}")
        return False


def update_reservation_status(phone, date, time, new_status):
    """Update the status of a specific reservation"""
    try:
        print("🔧 DEBUG - Starting reservation status update...")
        print(f"🔧 DEBUG - Status update parameters: phone={phone}, date={date}, time={time}")
        print(f"🔧 DEBUG - New status: {new_status}")
        
        sheet = init_google_sheets()
        if not sheet:
            print("🔧 DEBUG - Sheet connection failed")
            return False
        
        print("🔧 DEBUG - Fetching all sheet values for status update search...")
        # Get all data
        all_values = sheet.get_all_values()
        print(f"🔧 DEBUG - Retrieved {len(all_values)} rows from sheet")
        
        # Find the row to update
        print("🔧 DEBUG - Searching for matching reservation to update status...")
        for i, row in enumerate(all_values):
            print(f"🔧 DEBUG - Checking row {i+1} for status update match...")
            
            if (len(row) >= 9 and 
                row[2].strip() == str(phone).strip() and  # Phone column
                row[5].strip() == str(date).strip() and   # Date column  
                row[6].strip() == str(time).strip() and   # Time column
                row[8].strip() == 'Confirmed'):           # Status column
                
                print(f"🔧 DEBUG - Found matching reservation at row {i+1}")
                print(f"🔧 DEBUG - Updating status in column 9 (Status column)")
                
                # Update status (column 9, index 8)
                sheet.update_cell(i + 1, 9, new_status)
                print(f"✅ Reservation status updated to '{new_status}' for {phone}")
                print("🔧 DEBUG - Status update completed successfully")
                return True
        
        print(f"❌ Reservation not found for phone {phone}")
        print("🔧 DEBUG - No matching reservation found for status update")
        return False
        
    except Exception as e:
        print(f"❌ Error updating reservation status: {e}")
        print(f"🔧 DEBUG - Status update failed with error type: {type(e)}")
        return False
