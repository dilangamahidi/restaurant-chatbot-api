"""
Utility functions for date and time management
"""
from datetime import datetime


def extract_value(param):
    """Extract value from Dialogflow parameters with robust checks - VERSION WITH DEBUG"""
    try:
        print(f"🔧 DEBUG - extract_value input: {param} (type: {type(param)})")
        
        # Handle None or empty parameters
        if param is None or param == '':
            print(f"🔧 DEBUG - extract_value: param is None or empty")
            return None
        elif isinstance(param, list):
            # If it's a list, take the first element
            first_item = param[0] if param and len(param) > 0 else None
            print(f"🔧 DEBUG - extract_value: list, first_item = {first_item}")
            if isinstance(first_item, dict):
                # If the first element is a dictionary, extract the value
                if 'name' in first_item and first_item['name']:
                    result = str(first_item['name']).strip()
                    print(f"🔧 DEBUG - extract_value: returning from dict.name = '{result}'")
                    return result
                elif 'value' in first_item and first_item['value']:
                    result = str(first_item['value']).strip()
                    print(f"🔧 DEBUG - extract_value: returning from dict.value = '{result}'")
                    return result
                else:
                    # Take the first non-empty value from the dictionary
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
            # If it's a dictionary, search in common keys
            if 'name' in param and param['name']:
                result = str(param['name']).strip()
                print(f"🔧 DEBUG - extract_value: returning from dict.name = '{result}'")
                return result
            elif 'value' in param and param['value']:
                result = str(param['value']).strip()
                print(f"🔧 DEBUG - extract_value: returning from dict.value = '{result}'")
                return result
            elif len(param) == 1:
                # If it has only one key, take that value
                value = list(param.values())[0]
                result = str(value).strip() if value not in ['', None] else None
                print(f"🔧 DEBUG - extract_value: returning single dict value = '{result}'")
                return result
            else:
                # Take the first non-empty value
                for value in param.values():
                    if value and str(value).strip():
                        result = str(value).strip()
                        print(f"🔧 DEBUG - extract_value: returning first non-empty = '{result}'")
                        return result
                print(f"🔧 DEBUG - extract_value: no valid value in multi-key dict")
                return None
        else:
            # If it's a string or other type
            clean_value = str(param).strip()
            result = clean_value if clean_value not in ['', 'None', 'null'] else None
            print(f"🔧 DEBUG - extract_value: returning string/other = '{result}'")
            return result
    except Exception as e:
        print(f"❌ Error in extract_value: {e}")
        print(f"❌ Param type: {type(param)}, value: {param}")
        return None


def convert_day_to_number(day_name):
    """Convert day name to number for ML model processing"""
    # Standard week mapping: Monday = 0, Sunday = 6
    days = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
        'friday': 4, 'saturday': 5, 'sunday': 6,
        'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6
    }
    return days.get(str(day_name).lower(), 5)  # Default to Saturday


def convert_time_to_hour_improved(time_str):
    """Improved version to convert time string to hour - WITHOUT LIMITATIONS"""
    try:
        time_str = str(time_str).lower().strip()
        print(f"🔧 DEBUG - convert_time_to_hour_improved input: '{time_str}'")
        
        # Remove extra spaces
        time_str = ' '.join(time_str.split())
        
        # Handle PM/AM format
        if 'pm' in time_str:
            # Extract the hour part
            hour_part = time_str.replace('pm', '').strip()
            if ':' in hour_part:
                hour = int(hour_part.split(':')[0])
            else:
                hour = int(hour_part)
            
            # Convert to 24h format
            if hour != 12:
                hour += 12
            print(f"🔧 DEBUG - PM conversion: {hour}")
            
        elif 'am' in time_str:
            # Extract the hour part
            hour_part = time_str.replace('am', '').strip()
            if ':' in hour_part:
                hour = int(hour_part.split(':')[0])
            else:
                hour = int(hour_part)
            
            # Convert 12 AM to 0 (midnight)
            if hour == 12:
                hour = 0
            print(f"🔧 DEBUG - AM conversion: {hour}")
            
        else:
            # 24h format or simple number
            if ':' in time_str:
                hour = int(time_str.split(':')[0])
            else:
                hour = int(time_str)
            print(f"🔧 DEBUG - 24h conversion: {hour}")
        
        return hour
            
    except Exception as e:
        print(f"❌ Error in convert_time_to_hour_improved: {e}")
        return 19  # Default to 7PM


def check_restaurant_hours(hour):
    """
    Check if the time is within restaurant operating hours
    Returns: (is_valid, message)
    """
    RESTAURANT_OPEN_HOUR = 9   # 9 AM
    RESTAURANT_CLOSE_HOUR = 21 # 9 PM
    
    print(f"🔧 DEBUG - check_restaurant_hours input: {hour}")
    
    if RESTAURANT_OPEN_HOUR <= hour <= RESTAURANT_CLOSE_HOUR:
        print(f"✅ Hour {hour} within restaurant hours ({RESTAURANT_OPEN_HOUR}-{RESTAURANT_CLOSE_HOUR})")
        return True, None
    else:
        print(f"❌ Hour {hour} outside restaurant hours ({RESTAURANT_OPEN_HOUR}-{RESTAURANT_CLOSE_HOUR})")
        
        # Generate appropriate error message based on time
        if hour < RESTAURANT_OPEN_HOUR:
            # Too early - before opening
            if hour == 0:
                time_attempted = "12:00 AM (midnight)"
            elif hour < 12:
                time_attempted = f"{hour}:00 AM"
            else:
                time_attempted = f"{hour}:00"
                
            message = f"Sorry, we're not open at {time_attempted}. Our restaurant is open from 9:00 AM to 9:00 PM. Please choose a time between 9 AM and 9 PM."
        else:
            # Too late - after closing
            if hour == 12:
                time_attempted = "12:00 PM (noon)"
            elif hour < 12:
                time_attempted = f"{hour}:00 AM"
            elif hour == 24 or hour == 0:
                time_attempted = "12:00 AM (midnight)"
            else:
                hour_12 = hour - 12 if hour > 12 else hour
                time_attempted = f"{hour_12}:00 PM"
                
            message = f"Sorry, we're not open at {time_attempted}. Our restaurant closes at 9:00 PM. Please choose a time between 9:00 AM and 9:00 PM."
        
        return False, message


def parse_dialogflow_datetime(date_param, time_param):
    """
    Parse date/time from Dialogflow AND Google Sheets - WITH TIME VALIDATION
    Returns: (day_of_week, hour_of_day, error_message)
    If error_message is not None, there was a validation error
    """
    try:
        day_of_week = 5  # Default to Saturday
        hour_of_day = 19  # Default to 7PM
        
        print(f"🔧 DEBUG - parse_dialogflow_datetime input: date='{date_param}', time='{time_param}'")
        print(f"🔧 DEBUG - date_param type: {type(date_param)}, time_param type: {type(time_param)}")
        
        # DATE PARSING - IMPROVED WITH TUESDAY FIX
        if date_param:
            date_str = str(date_param).strip()
            print(f"🔧 DEBUG - Processing date: '{date_str}'")
            
            # 🚨 CRITICAL FIX: Check ISO format more specifically
            # Can't just check 'T' in date_str because "Tuesday" starts with T!
            # Must be YYYY-MM-DDTHH:MM:SS format
            is_iso_format = (
                'T' in date_str and 
                len(date_str) > 10 and 
                date_str[4] == '-' and 
                date_str[7] == '-' and
                date_str[10] == 'T'
            )
            
            print(f"🔧 DEBUG - is_iso_format check: {is_iso_format}")
            
            if is_iso_format:
                # ISO format from Dialogflow (2025-06-23T12:00:00+02:00)
                clean_date = date_str.split('T')[0]
                parsed_date = datetime.strptime(clean_date, '%Y-%m-%d')
                day_of_week = parsed_date.weekday()
                print(f"🔧 DEBUG - Parsed ISO date: {clean_date}, weekday: {day_of_week}")
                
            elif len(date_str) == 10 and date_str.count('-') == 2:
                # YYYY-MM-DD format
                parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                day_of_week = parsed_date.weekday()
                print(f"🔧 DEBUG - Parsed YYYY-MM-DD date, weekday: {day_of_week}")
                
            elif ',' in date_str:
                # Readable format from Google Sheets (Tuesday, June 24, 2025)
                print(f"🔧 DEBUG - Attempting to parse readable date: '{date_str}'")
                
                try:
                    # Try complete format with day of week
                    parsed_date = datetime.strptime(date_str, '%A, %B %d, %Y')
                    day_of_week = parsed_date.weekday()
                    print(f"🔧 DEBUG - SUCCESS: Parsed readable format 1, date: {parsed_date}, weekday: {day_of_week}")
                    
                    # Verify that the day of the week matches
                    expected_day = date_str.split(',')[0].strip()
                    actual_day = parsed_date.strftime('%A')
                    if expected_day.lower() != actual_day.lower():
                        print(f"⚠️ WARNING: Day mismatch! Expected: {expected_day}, Got: {actual_day}")
                        # Use the calculated day from the date, not the one in the name
                        day_of_week = parsed_date.weekday()
                    else:
                        print(f"✅ Day verification passed: {expected_day} = {actual_day}")
                    
                except ValueError as e1:
                    print(f"🔧 DEBUG - Format 1 failed: {e1}")
                    try:
                        # Try format without day of week
                        date_without_day = date_str.split(',', 1)[1].strip() if ',' in date_str else date_str
                        print(f"🔧 DEBUG - Trying format 2 with: '{date_without_day}'")
                        parsed_date = datetime.strptime(date_without_day, '%B %d, %Y')
                        day_of_week = parsed_date.weekday()
                        print(f"🔧 DEBUG - SUCCESS: Parsed readable format 2, weekday: {day_of_week}")
                        
                    except ValueError as e2:
                        print(f"🔧 DEBUG - Format 2 also failed: {e2}")
                        
                        # ROBUST FALLBACK: Manually extract day of week
                        if ',' in date_str:
                            day_name = date_str.split(',')[0].strip().lower()
                            manual_day_mapping = {
                                'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                                'friday': 4, 'saturday': 5, 'sunday': 6
                            }
                            
                            if day_name in manual_day_mapping:
                                day_of_week = manual_day_mapping[day_name]
                                print(f"🔧 DEBUG - FALLBACK SUCCESS: Manual mapping '{day_name}' -> {day_of_week}")
                            else:
                                print(f"❌ Could not parse date format: {date_str}")
                        else:
                            print(f"❌ Could not parse date format: {date_str}")
                            
            else:
                print(f"❌ Unknown date format: {date_str}")
        
        # TIME PARSING - WITH VALIDATION INSTEAD OF AUTOMATIC LIMITATIONS
        if time_param:
            time_str = str(time_param).strip()
            print(f"🔧 DEBUG - Processing time: '{time_str}'")
            
            # Same improved check for time format
            is_iso_time_format = (
                'T' in time_str and 
                len(time_str) > 10 and 
                time_str[4] == '-' and 
                time_str[7] == '-' and
                time_str[10] == 'T'
            )
            
            if is_iso_time_format:
                # ISO format from Dialogflow
                time_part = time_str.split('T')[1].split('+')[0].split('-')[0]  # Handle both +02:00 and -05:00
                parsed_hour = int(time_part.split(':')[0])
                print(f"🔧 DEBUG - Parsed ISO time: {time_part}, parsed_hour: {parsed_hour}")
                
                # 🆕 VALIDATION INSTEAD OF AUTOMATIC CONVERSION
                is_valid, error_msg = check_restaurant_hours(parsed_hour)
                if not is_valid:
                    print(f"❌ Time validation failed: {error_msg}")
                    return day_of_week, parsed_hour, error_msg
                hour_of_day = parsed_hour
                
            elif 'AM' in time_str.upper() or 'PM' in time_str.upper():
                # 12h format from Google Sheets (12:00 PM)
                parsed_hour = convert_time_to_hour_improved(time_str)
                print(f"🔧 DEBUG - Parsed 12h time: {time_str}, parsed_hour: {parsed_hour}")
                
                # 🆕 VALIDATION INSTEAD OF AUTOMATIC CONVERSION
                is_valid, error_msg = check_restaurant_hours(parsed_hour)
                if not is_valid:
                    print(f"❌ Time validation failed: {error_msg}")
                    return day_of_week, parsed_hour, error_msg
                hour_of_day = parsed_hour
                
            elif ':' in time_str:
                # 24h format (19:30)
                parsed_hour = int(time_str.split(':')[0])
                print(f"🔧 DEBUG - Parsed 24h time: {time_str}, parsed_hour: {parsed_hour}")
                
                # 🆕 VALIDATION INSTEAD OF AUTOMATIC CONVERSION
                is_valid, error_msg = check_restaurant_hours(parsed_hour)
                if not is_valid:
                    print(f"❌ Time validation failed: {error_msg}")
                    return day_of_week, parsed_hour, error_msg
                hour_of_day = parsed_hour
                
            else:
                # Just a number (19)
                try:
                    parsed_hour = int(time_str)
                    print(f"🔧 DEBUG - Parsed simple hour: {parsed_hour}")
                    
                    # 🆕 VALIDATION INSTEAD OF AUTOMATIC CONVERSION
                    is_valid, error_msg = check_restaurant_hours(parsed_hour)
                    if not is_valid:
                        print(f"❌ Time validation failed: {error_msg}")
                        return day_of_week, parsed_hour, error_msg
                    hour_of_day = parsed_hour
                    
                except ValueError:
                    print(f"❌ Could not parse time: {time_str}")
                    hour_of_day = 19  # Default if not parseable
        
        # FINAL DEBUG OUTPUT
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_name = day_names[day_of_week] if 0 <= day_of_week <= 6 else 'Invalid'
        
        print(f"🔧 DEBUG - FINAL RESULT: day_of_week={day_of_week} ({day_name}), hour_of_day={hour_of_day}")
        
        # FINAL VALIDATION
        if not (0 <= day_of_week <= 6):
            print(f"⚠️ Invalid day_of_week: {day_of_week}, using default 5 (Saturday)")
            day_of_week = 5
            
        if not (0 <= hour_of_day <= 23):
            print(f"⚠️ Invalid hour_of_day: {hour_of_day}, using default 19 (7PM)")
            hour_of_day = 19
        
        return day_of_week, hour_of_day, None  # None = no error
        
    except Exception as e:
        print(f"❌ Error in parse_dialogflow_datetime: {e}")
        import traceback
        print(f"❌ TRACEBACK: {traceback.format_exc()}")
        return 5, 19, f"Sorry, I had trouble understanding the date or time. Please try again."


def format_date_readable(date_string):
    """
    Convert date from ISO format to readable format
    """
    if not date_string:
        return ""
    
    try:
        # If it's in ISO format (2025-06-23T12:00:00+02:00)
        if 'T' in str(date_string):
            date_part = str(date_string).split('T')[0]
            date_obj = datetime.strptime(date_part, '%Y-%m-%d')
        else:
            # If it's just the date (2025-06-23)
            date_obj = datetime.strptime(str(date_string), '%Y-%m-%d')
        
        # Format as "Monday, June 23, 2025"
        return date_obj.strftime('%A, %B %d, %Y')
    except:
        # If it can't parse, return the original
        return str(date_string)


def format_time_readable(time_string):
    """
    Convert time from ISO format to readable format
    """
    if not time_string:
        return ""
    
    try:
        # If it's in complete ISO format (2025-06-22T12:00:00+02:00)
        if 'T' in str(time_string):
            time_part = str(time_string).split('T')[1].split('+')[0]
            hour = int(time_part.split(':')[0])
            minute = int(time_part.split(':')[1])
        else:
            # If it's just the time (12:00 or 12)
            time_str = str(time_string).strip()
            if ':' in time_str:
                hour = int(time_str.split(':')[0])
                minute = int(time_str.split(':')[1]) if len(time_str.split(':')) > 1 else 0
            else:
                hour = int(time_str)
                minute = 0
        
        # Convert to 12h format with AM/PM
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
        # If it can't parse, return the original
        return str(time_string)
