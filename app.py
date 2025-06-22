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

app = Flask(__name__)
CORS(app)

# Initialize services
try:
    model = joblib.load('restaurant_model_client.pkl')
except:
    model = None

RESTAURANT_INFO = {
    "name": "Restoran",
    "phone": "0764272635", 
    "email": "dilangakavindu123@gmail.com",
    "address": "Aluthgoga Road, Mawella, Nakulugamuwa, Matara",
    "description": "Matara's home of authentic Sri Lankan flavor"
}

MENU = {
    "breakfast": ["String Hoppers with Curry", "Milk Rice (Kiribath)", "Coconut Roti with Sambol", "Ceylon Tea"],
    "lunch": ["Rice and Curry", "Kottu Roti", "Fried Rice", "Hoppers with Egg"], 
    "dinner": ["Fish Curry", "Chicken Curry", "Seafood Platter", "Vegetarian Curry"],
    "beverages": ["King Coconut", "Ceylon Tea", "Fresh Juices", "Local Beer"]
}

# ================================================================
# UTILITY FUNCTIONS - CONSOLIDATED
# ================================================================

def extract_value(param):
    """Universal parameter extractor - FIXED"""
    try:
        if not param:
            return None
        if isinstance(param, list):
            if param and len(param) > 0:
                first_item = param[0]
                if isinstance(first_item, dict):
                    return str(first_item.get('name') or first_item.get('value') or '').strip()
                else:
                    return str(first_item).strip()
        elif isinstance(param, dict):
            return str(param.get('name') or param.get('value') or list(param.values())[0] if param.values() else '').strip()
        else:
            return str(param).strip()
    except:
        return None

def parse_number(value):
    """Universal number parser - FIXED"""
    try:
        if not value:
            return None
        
        # Word to number mapping
        word_map = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
            'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15, 'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20
        }
        
        clean_val = str(value).lower().strip()
        # Remove common words
        for word in ['guests', 'people', 'table', 'number']:
            clean_val = clean_val.replace(word, '').strip()
        
        # Check word mapping first
        if clean_val in word_map:
            return word_map[clean_val]
        
        # Try direct conversion
        if clean_val.isdigit():
            return int(clean_val)
        
        # Try float conversion
        try:
            return int(float(clean_val))
        except:
            return None
            
    except:
        return None

def parse_datetime(date_str, time_str):
    """Universal datetime parser - FIXED"""
    try:
        day_of_week, hour_of_day = 5, 19  # defaults
        
        # Parse date
        if date_str:
            date_lower = str(date_str).lower().strip()
            if 'monday' in date_lower: day_of_week = 0
            elif 'tuesday' in date_lower: day_of_week = 1
            elif 'wednesday' in date_lower: day_of_week = 2
            elif 'thursday' in date_lower: day_of_week = 3
            elif 'friday' in date_lower: day_of_week = 4
            elif 'saturday' in date_lower: day_of_week = 5
            elif 'sunday' in date_lower: day_of_week = 6
            elif 'T' in str(date_str):
                try:
                    date_obj = datetime.strptime(str(date_str).split('T')[0], '%Y-%m-%d')
                    day_of_week = date_obj.weekday()
                except:
                    pass
            elif ',' in str(date_str):
                try:
                    date_obj = datetime.strptime(str(date_str), '%A, %B %d, %Y')
                    day_of_week = date_obj.weekday()
                except:
                    try:
                        date_obj = datetime.strptime(str(date_str), '%B %d, %Y') 
                        day_of_week = date_obj.weekday()
                    except:
                        pass
            elif len(str(date_str)) == 10 and str(date_str).count('-') == 2:
                try:
                    date_obj = datetime.strptime(str(date_str), '%Y-%m-%d')
                    day_of_week = date_obj.weekday()
                except:
                    pass
        
        # Parse time
        if time_str:
            time_clean = str(time_str).lower().strip()
            try:
                if 'pm' in time_clean:
                    hour = int(time_clean.replace('pm', '').replace(':', '').strip())
                    hour_of_day = hour + 12 if hour != 12 else 12
                elif 'am' in time_clean:
                    hour = int(time_clean.replace('am', '').replace(':', '').strip())
                    hour_of_day = 0 if hour == 12 else hour
                elif ':' in time_clean:
                    hour_of_day = int(time_clean.split(':')[0])
                elif time_clean.isdigit():
                    hour_of_day = int(time_clean)
                elif 'T' in str(time_str):
                    hour_of_day = int(str(time_str).split('T')[1].split(':')[0])
            except:
                pass
        
        return day_of_week, hour_of_day
    except:
        return 5, 19
# VERSIONE CORRETTA - Sostituisci queste funzioni nel tuo codice

def extract_value(param):
    """Universal parameter extractor - FIXED"""
    try:
        if not param:
            return None
        if isinstance(param, list):
            if param and len(param) > 0:
                first_item = param[0]
                if isinstance(first_item, dict):
                    return str(first_item.get('name') or first_item.get('value') or '').strip()
                else:
                    return str(first_item).strip()
        elif isinstance(param, dict):
            return str(param.get('name') or param.get('value') or list(param.values())[0] if param.values() else '').strip()
        else:
            return str(param).strip()
    except:
        return None

def parse_number(value):
    """Universal number parser - FIXED"""
    try:
        if not value:
            return None
        
        # Word to number mapping
        word_map = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
            'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15, 'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20
        }
        
        clean_val = str(value).lower().strip()
        # Remove common words
        for word in ['guests', 'people', 'table', 'number']:
            clean_val = clean_val.replace(word, '').strip()
        
        # Check word mapping first
        if clean_val in word_map:
            return word_map[clean_val]
        
        # Try direct conversion
        if clean_val.isdigit():
            return int(clean_val)
        
        # Try float conversion
        try:
            return int(float(clean_val))
        except:
            return None
            
    except:
        return None

def parse_datetime(date_str, time_str):
    """Universal datetime parser - FIXED"""
    try:
        day_of_week, hour_of_day = 5, 19  # defaults
        
        # Parse date
        if date_str:
            date_lower = str(date_str).lower().strip()
            if 'monday' in date_lower: day_of_week = 0
            elif 'tuesday' in date_lower: day_of_week = 1
            elif 'wednesday' in date_lower: day_of_week = 2
            elif 'thursday' in date_lower: day_of_week = 3
            elif 'friday' in date_lower: day_of_week = 4
            elif 'saturday' in date_lower: day_of_week = 5
            elif 'sunday' in date_lower: day_of_week = 6
            elif 'T' in str(date_str):
                try:
                    date_obj = datetime.strptime(str(date_str).split('T')[0], '%Y-%m-%d')
                    day_of_week = date_obj.weekday()
                except:
                    pass
            elif ',' in str(date_str):
                try:
                    date_obj = datetime.strptime(str(date_str), '%A, %B %d, %Y')
                    day_of_week = date_obj.weekday()
                except:
                    try:
                        date_obj = datetime.strptime(str(date_str), '%B %d, %Y') 
                        day_of_week = date_obj.weekday()
                    except:
                        pass
            elif len(str(date_str)) == 10 and str(date_str).count('-') == 2:
                try:
                    date_obj = datetime.strptime(str(date_str), '%Y-%m-%d')
                    day_of_week = date_obj.weekday()
                except:
                    pass
        
        # Parse time
        if time_str:
            time_clean = str(time_str).lower().strip()
            try:
                if 'pm' in time_clean:
                    hour = int(time_clean.replace('pm', '').replace(':', '').strip())
                    hour_of_day = hour + 12 if hour != 12 else 12
                elif 'am' in time_clean:
                    hour = int(time_clean.replace('am', '').replace(':', '').strip())
                    hour_of_day = 0 if hour == 12 else hour
                elif ':' in time_clean:
                    hour_of_day = int(time_clean.split(':')[0])
                elif time_clean.isdigit():
                    hour_of_day = int(time_clean)
                elif 'T' in str(time_str):
                    hour_of_day = int(str(time_str).split('T')[1].split(':')[0])
            except:
                pass
        
        return day_of_week, hour_of_day
    except:
        return 5, 19

def format_datetime(date_str, time_str):
    """Format datetime for display - FIXED"""
    try:
        # Format date
        if 'T' in str(date_str):
            try:
                date_obj = datetime.strptime(str(date_str).split('T')[0], '%Y-%m-%d')
                formatted_date = date_obj.strftime('%A, %B %d, %Y')
            except:
                formatted_date = str(date_str)
        elif str(date_str).lower() in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
            # For day names, we need to calculate the next occurrence
            from datetime import datetime, timedelta
            today = datetime.now()
            days_ahead = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'].index(str(date_str).lower()) - today.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            target_date = today + timedelta(days=days_ahead)
            formatted_date = target_date.strftime('%A, %B %d, %Y')
        else:
            formatted_date = str(date_str)
        
        # Format time
        try:
            time_clean = str(time_str).lower().strip()
            if 'pm' in time_clean:
                hour = int(time_clean.replace('pm', '').replace(':', '').strip())
                if hour == 12:
                    formatted_time = "12:00 PM"
                else:
                    formatted_time = f"{hour}:00 PM"
            elif 'am' in time_clean:
                hour = int(time_clean.replace('am', '').replace(':', '').strip())
                if hour == 12:
                    formatted_time = "12:00 AM"
                else:
                    formatted_time = f"{hour}:00 AM"
            elif 'T' in str(time_str):
                hour = int(str(time_str).split('T')[1].split(':')[0])
                if hour == 0:
                    formatted_time = "12:00 AM"
                elif hour < 12:
                    formatted_time = f"{hour}:00 AM"
                elif hour == 12:
                    formatted_time = "12:00 PM"
                else:
                    formatted_time = f"{hour-12}:00 PM"
            else:
                hour = int(str(time_str).split(':')[0]) if ':' in str(time_str) else int(time_str)
                if hour == 0:
                    formatted_time = "12:00 AM"
                elif hour < 12:
                    formatted_time = f"{hour}:00 AM"
                elif hour == 12:
                    formatted_time = "12:00 PM"
                else:
                    formatted_time = f"{hour-12}:00 PM"
        except:
            formatted_time = str(time_str)
            
        return formatted_date, formatted_time
    except Exception as e:
        print(f"Format error: {e}")
        return str(date_str), str(time_str)
        
def build_response(messages):
    """Universal response builder"""
    if isinstance(messages, str):
        return jsonify({'fulfillmentText': messages})
    
    return jsonify({
        'fulfillmentText': messages[0],
        'fulfillmentMessages': [{'text': {'text': [msg]}} for msg in messages]
    })

# ================================================================
# ML & SHEETS SERVICES - OPTIMIZED
# ================================================================

def get_sheet():
    """Get Google Sheets connection"""
    try:
        creds_json = os.environ.get('GOOGLE_CREDENTIALS')
        if creds_json:
            creds_dict = json.loads(creds_json)
            creds = Credentials.from_service_account_info(creds_dict, scopes=[
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ])
        else:
            creds = Credentials.from_service_account_file('credentials.json', scopes=[
                'https://www.googleapis.com/auth/spreadsheets', 
                'https://www.googleapis.com/auth/drive'
            ])
        
        client = gspread.authorize(creds)
        return client.open_by_key("1QTaGoxeQur4Rh03tJETcRwExbmTvU1FF6TE1v0UjuMk").sheet1
    except:
        return None

def find_available_table(guests, day_of_week, hour_of_day):
    """Find best available table using ML"""
    if not model:
        return {'available': False}
    
    available_tables = []
    for table_id in range(1, 21):
        input_data = np.array([[table_id, guests, day_of_week, hour_of_day]])
        if model.predict(input_data)[0] == 0:  # 0 = available
            available_tables.append(table_id)
    
    if not available_tables:
        return {'available': False}
    
    # Select best table based on guest count
    if guests <= 2:
        best_tables = [t for t in available_tables if t <= 8]
    elif guests <= 4:
        best_tables = [t for t in available_tables if 9 <= t <= 15] 
    else:
        best_tables = [t for t in available_tables if t >= 16]
    
    best_table = best_tables[0] if best_tables else available_tables[0]
    return {'available': True, 'table_number': best_table, 'total_available': len(available_tables)}

def get_user_reservations(phone):
    """Get user's reservations"""
    sheet = get_sheet()
    if not sheet:
        return []
    
    try:
        records = sheet.get_all_records()
        return [r for r in records if str(r.get('Phone', '')).strip() == str(phone).strip() and r.get('Status') == 'Confirmed']
    except:
        return []

def save_reservation(data):
    """Save reservation to sheets"""
    sheet = get_sheet()
    if not sheet:
        return False
    
    try:
        row_data = [
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            data['name'], data['phone'], data['email'], data['guests'],
            data['date'], data['time'], data['table'], 'Confirmed'
        ]
        sheet.append_row(row_data)
        return True
    except:
        return False

def update_reservation_field(phone, date, time, field, new_value):
    """Update reservation field"""
    sheet = get_sheet()
    if not sheet:
        return False
    
    try:
        all_values = sheet.get_all_values()
        field_map = {'date': 6, 'time': 7, 'guests': 5, 'table': 8}
        
        for i, row in enumerate(all_values):
            if (len(row) >= 9 and row[2].strip() == str(phone).strip() and 
                row[5].strip() == str(date).strip() and row[6].strip() == str(time).strip() and
                row[8].strip() == 'Confirmed'):
                
                if field in field_map:
                    sheet.update_cell(i + 1, field_map[field], new_value)
                    return True
        return False
    except:
        return False

# ================================================================
# HANDLERS - CONSOLIDATED
# ================================================================

def handle_make_reservation(params):
    """Create new reservation - FIXED VERSION"""
    try:
        print(f"DEBUG: Raw params = {params}")
        
        # Extract parameters with multiple possible keys
        name = (extract_value(params.get('name')) or 
                extract_value(params.get('person')) or 
                extract_value(params.get('given-name')))
        
        phone = (extract_value(params.get('phone_number')) or 
                 extract_value(params.get('phone')) or 
                 extract_value(params.get('number')))
        
        email = extract_value(params.get('email'))
        
        # Try multiple keys for guests
        guests_raw = (extract_value(params.get('guest_count')) or 
                      extract_value(params.get('guests')) or 
                      extract_value(params.get('number-integer')) or
                      extract_value(params.get('number')))
        guests = parse_number(guests_raw) or 2
        
        # Try multiple keys for date
        date = (extract_value(params.get('day_of_week')) or 
                extract_value(params.get('date')) or
                extract_value(params.get('date-time')))
        
        # Try multiple keys for time  
        time = (extract_value(params.get('hour_of_day')) or 
                extract_value(params.get('time')) or
                extract_value(params.get('date-time')))
        
        print(f"DEBUG: Extracted - name={name}, phone={phone}, email={email}, guests={guests}, date={date}, time={time}")
        
        # Validate
        errors = []
        if not name or len(name) < 2: 
            errors.append("your name")
        if not phone: 
            errors.append("your phone number")
        if not email or '@' not in email: 
            errors.append("your email address")
        if not date: 
            errors.append("the date")
        if not time: 
            errors.append("the time")
        if guests < 1 or guests > 20: 
            errors.append("valid guest count (1-20)")
        
        if errors:
            return build_response(f"I need {', '.join(errors)} to complete your reservation.")
        
        # Format datetime
        formatted_date, formatted_time = format_datetime(date, time)
        print(f"DEBUG: Formatted - date={formatted_date}, time={formatted_time}")
        
        # Check availability
        day_of_week, hour_of_day = parse_datetime(date, time)
        print(f"DEBUG: Parsed for ML - day={day_of_week}, hour={hour_of_day}")
        
        availability = find_available_table(guests, day_of_week, hour_of_day)
        print(f"DEBUG: Availability = {availability}")
        
        if not availability['available']:
            return build_response(f"Sorry, no tables available for {guests} guests at {formatted_time} on {formatted_date}. Please try a different time.")
        
        # Save reservation
        reservation_data = {
            'name': name, 
            'phone': phone, 
            'email': email, 
            'guests': guests,
            'date': formatted_date, 
            'time': formatted_time, 
            'table': availability['table_number']
        }
        
        print(f"DEBUG: Saving reservation = {reservation_data}")
        
        if save_reservation(reservation_data):
            return build_response([
                "🎉 Reservation Confirmed!",
                f"👤 Name: {name}",
                f"📞 Phone: {phone}", 
                f"📧 Email: {email}",
                f"👥 Guests: {guests}",
                f"📅 Date: {formatted_date}",
                f"🕐 Time: {formatted_time}",
                f"🪑 Table: {availability['table_number']}"
            ])
        else:
            return build_response(f"Reservation created but please call {RESTAURANT_INFO['phone']} to confirm")
            
    except Exception as e:
        print(f"ERROR in handle_make_reservation: {e}")
        import traceback
        print(f"TRACEBACK: {traceback.format_exc()}")
        return build_response(f"Sorry, technical error. Please call {RESTAURANT_INFO['phone']}")

def handle_modify_reservation(intent_name, params):
    """Universal modification handler - REPLACES 3 SEPARATE FUNCTIONS"""
    phone = extract_value(params.get('phone_number') or params.get('phone'))
    if not phone:
        return build_response("Please provide your phone number")
    
    reservations = get_user_reservations(phone)
    if not reservations:
        return build_response(f"No reservations found for {phone}")
    if len(reservations) != 1:
        return build_response(f"Multiple reservations found. Call {RESTAURANT_INFO['phone']}")
    
    reservation = reservations[0]
    old_date, old_time, old_guests = reservation['Date'], reservation['Time'], reservation['Guests']
    
    # Determine what to modify based on intent
    if 'guests' in intent_name:
        new_guests = parse_number(extract_value(params.get('new_guests') or params.get('guests') or params.get('number')))
        if not new_guests or new_guests < 1 or new_guests > 20:
            return build_response("Please specify valid guest count (1-20)")
        
        day_of_week, hour_of_day = parse_datetime(old_date, old_time)
        availability = find_available_table(new_guests, day_of_week, hour_of_day)
        
        if availability['available']:
            update_reservation_field(phone, old_date, old_time, 'guests', new_guests)
            update_reservation_field(phone, old_date, old_time, 'table', availability['table_number'])
            return build_response([
                "✅ Guest count updated!",
                f"👥 New guests: {new_guests}",
                f"🪑 New table: {availability['table_number']}"
            ])
        else:
            return build_response(f"No availability for {new_guests} guests at that time")
    
    elif 'time' in intent_name:
        new_time = extract_value(params.get('new_time') or params.get('time'))
        if not new_time:
            return build_response("Please specify new time")
        
        formatted_date, formatted_time = format_datetime(old_date, new_time)
        day_of_week, hour_of_day = parse_datetime(old_date, new_time)
        availability = find_available_table(int(old_guests), day_of_week, hour_of_day)
        
        if availability['available']:
            update_reservation_field(phone, old_date, old_time, 'time', formatted_time)
            update_reservation_field(phone, old_date, formatted_time, 'table', availability['table_number'])
            return build_response([
                "✅ Time updated!",
                f"🕐 New time: {formatted_time}",
                f"🪑 New table: {availability['table_number']}"
            ])
        else:
            return build_response(f"No availability at {formatted_time}")
    
    elif 'date' in intent_name:
        new_date = extract_value(params.get('new_date') or params.get('date'))
        if not new_date:
            return build_response("Please specify new date")
        
        formatted_date, _ = format_datetime(new_date, old_time)
        day_of_week, hour_of_day = parse_datetime(new_date, old_time)
        availability = find_available_table(int(old_guests), day_of_week, hour_of_day)
        
        if availability['available']:
            update_reservation_field(phone, old_date, old_time, 'date', formatted_date)
            update_reservation_field(phone, formatted_date, old_time, 'table', availability['table_number'])
            return build_response([
                "✅ Date updated!",
                f"📅 New date: {formatted_date}",
                f"🪑 New table: {availability['table_number']}"
            ])
        else:
            return build_response(f"No availability on {formatted_date}")
    
    else:
        # Show modification menu
        return build_response([
            "📋 Current reservation:",
            f"👤 {reservation['Name']} - 📅 {old_date} - 🕐 {old_time} - 👥 {old_guests}",
            "What would you like to modify?",
            "Say: 'Change time to 8pm' or 'Change to 4 guests' or 'Change date to tomorrow'"
        ])

def handle_info_requests(intent_name):
    """Handle all info requests - CONSOLIDATED"""
    if intent_name == 'show.menu':
        return build_response([
            f"🍽️ {RESTAURANT_INFO['name']} Menu:",
            f"☀️ BREAKFAST: {', '.join(MENU['breakfast'])}",
            f"🍛 LUNCH: {', '.join(MENU['lunch'])}",
            f"🌅 DINNER: {', '.join(MENU['dinner'])}",
            f"🥤 BEVERAGES: {', '.join(MENU['beverages'])}"
        ])
    elif intent_name == 'opening.hours':
        return build_response([
            f"🕐 {RESTAURANT_INFO['name']} Hours:",
            "📅 Monday-Saturday: 9AM-9PM",
            "📅 Sunday: 10AM-8PM"
        ])
    elif intent_name == 'restaurant.info':
        return build_response([
            f"🍽️ {RESTAURANT_INFO['name']}",
            RESTAURANT_INFO['description'],
            f"📍 {RESTAURANT_INFO['address']}",
            f"📞 {RESTAURANT_INFO['phone']}",
            f"📧 {RESTAURANT_INFO['email']}"
        ])

# ================================================================
# MAIN WEBHOOK - SIMPLIFIED
# ================================================================

@app.route('/dialogflow-webhook', methods=['POST'])
def dialogflow_webhook():
    try:
        req = request.get_json()
        intent_name = req.get('queryResult', {}).get('intent', {}).get('displayName', '')
        parameters = req.get('queryResult', {}).get('parameters', {})
        
        print(f"DEBUG: Intent = {intent_name}")
        print(f"DEBUG: Parameters = {parameters}")
        
        if intent_name == 'make.reservation':
            return handle_make_reservation(parameters)
        elif intent_name.startswith('modify.reservation'):
            return handle_modify_reservation(intent_name, parameters)
        elif intent_name in ['show.menu', 'opening.hours', 'restaurant.info']:
            return handle_info_requests(intent_name)
        elif intent_name == 'check.my.reservation':
            phone = extract_value(parameters.get('phone_number') or parameters.get('phone'))
            if not phone:
                return build_response("Please provide your phone number to check your reservation")
            reservations = get_user_reservations(phone)
            if reservations:
                res = reservations[0]
                return build_response([
                    "📋 Your reservation:",
                    f"👤 {res['Name']} - 📞 {res['Phone']}",
                    f"📅 {res['Date']} - 🕐 {res['Time']}",
                    f"👥 {res['Guests']} guests - 🪑 Table {res['Table']}"
                ])
            else:
                return build_response(f"No reservations found for {phone}")
        elif intent_name == 'check.availability':
            # Handle availability check
            guests = parse_number(extract_value(parameters.get('guest_count') or parameters.get('guests'))) or 2
            date = extract_value(parameters.get('date') or parameters.get('day_of_week'))
            time = extract_value(parameters.get('time') or parameters.get('hour_of_day'))
            
            if not date or not time:
                return build_response("Please specify both date and time to check availability")
            
            day_of_week, hour_of_day = parse_datetime(date, time)
            availability = find_available_table(guests, day_of_week, hour_of_day)
            formatted_date, formatted_time = format_datetime(date, time)
            
            if availability['available']:
                return build_response(f"✅ Yes! We have availability for {guests} guests on {formatted_date} at {formatted_time}. Would you like to make a reservation?")
            else:
                return build_response(f"❌ Sorry, no availability for {guests} guests on {formatted_date} at {formatted_time}. Please try a different time.")
        elif intent_name == 'cancel.reservation':
            phone = extract_value(parameters.get('phone_number') or parameters.get('phone'))
            if not phone:
                return build_response("Please provide your phone number to cancel your reservation")
            # Add cancel logic here
            return build_response(f"To cancel your reservation, please call us at {RESTAURANT_INFO['phone']}")
        else:
            return build_response(f"🍽️ Welcome to {RESTAURANT_INFO['name']}! I can help you make reservations, check availability, or provide information. How can I assist you?")
            
    except Exception as e:
        print(f"ERROR in webhook: {e}")
        import traceback
        print(f"TRACEBACK: {traceback.format_exc()}")
        return build_response(f"Technical error. Please call {RESTAURANT_INFO['phone']}")

@app.route('/')
def home():
    return jsonify({'message': f'{RESTAURANT_INFO["name"]} API Running!', 'model_loaded': model is not None})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
