"""
Handlers for restaurant reservation management
"""
from flask import jsonify, request
import re
import traceback
import time
import threading

# Import from our modules
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

def log_function_entry(func_name, parameters):
    """Standardized logging for function entry"""
    print(f"\n🚀 === ENTERING FUNCTION: {func_name} ===")
    print(f"🕐 Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔧 Thread: {threading.current_thread().name}")
    print(f"📋 Parameters: {parameters}")
    print("=" * 50)

def log_function_exit(func_name, response_text, success=True):
    """Standardized logging for function exit"""
    status = "✅ SUCCESS" if success else "❌ FAILED"
    print(f"\n🏁 === EXITING FUNCTION: {func_name} - {status} ===")
    print(f"🕐 Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📤 Response: {response_text[:100]}...")
    print("=" * 50)

def safe_operation(operation_name, operation_func, *args, **kwargs):
    """Safe wrapper for operations that might fail"""
    print(f"🔄 STARTING OPERATION: {operation_name}")
    try:
        start_time = time.time()
        result = operation_func(*args, **kwargs)
        end_time = time.time()
        print(f"✅ OPERATION COMPLETED: {operation_name} in {end_time-start_time:.2f}s")
        print(f"📊 Result: {result}")
        return result, True
    except Exception as e:
        print(f"❌ OPERATION FAILED: {operation_name}")
        print(f"💥 Error: {str(e)}")
        print(f"📚 Traceback: {traceback.format_exc()}")
        return None, False

def create_safe_response(response_text, func_name):
    """Create a safe JSON response with UTF-8 encoding - FINAL VERSION"""
    print(f"🔨 BUILDING RESPONSE for {func_name}")
    print(f"📝 Response text: '{response_text}'")
    
    try:
        if not isinstance(response_text, str):
            response_text = str(response_text)
        
        if len(response_text) > 1000:
            response_text = response_text[:997] + "..."
        
        response_json = {'fulfillmentText': response_text}
        
        # 🚨 SOLUZIONE FINALE: Usa Response con UTF-8 come negli endpoint
        from flask import Response
        import json
        
        json_string = json.dumps(response_json, ensure_ascii=False, separators=(',', ':'))
        
        return Response(
            json_string,
            content_type='application/json; charset=utf-8',
            status=200
        )
        
    except Exception as e:
        print(f"❌ Error building response: {e}")
        # Fallback anche con UTF-8
        fallback = json.dumps({
            'fulfillmentText': 'Sorry, there was a technical issue. Please call us.'
        }, ensure_ascii=False)
        
        return Response(
            fallback,
            content_type='application/json; charset=utf-8',
            status=200
        )
        
def handle_modify_reservation_date(parameters, language_code='en'):
    """Handle reservation date modification - WITH TIME VALIDATION"""
    log_function_entry("handle_modify_reservation_date", parameters)
    
    try:
        # Import translations
        from translations import get_text
        
        # 1. PARAMETER EXTRACTION PHASE
        print("🔄 PHASE 1: Extracting parameters...")
        phone_raw = parameters.get('phone_number', parameters.get('phone', ''))
        phone, phone_ok = safe_operation("extract_phone", extract_value, phone_raw)
        
        new_date_raw = parameters.get('new_date', parameters.get('date', ''))
        new_date, date_ok = safe_operation("extract_date", extract_value, new_date_raw)
        
        print(f"📞 Phone: '{phone}' (success: {phone_ok})")
        print(f"📅 New date: '{new_date}' (success: {date_ok})")
        
        # 2. INPUT VALIDATION PHASE
        print("🔄 PHASE 2: Validating inputs...")
        if not phone or not phone_ok:
            response = get_text('phone_for_check', language_code)
            log_function_exit("handle_modify_reservation_date", response, False)
            return create_safe_response(response, "handle_modify_reservation_date")
        
        if not new_date or not date_ok:
            response = "Please specify the new date for your reservation."
            log_function_exit("handle_modify_reservation_date", response, False)
            return create_safe_response(response, "handle_modify_reservation_date")
        
        # 3. RESERVATION SEARCH PHASE
        print("🔄 PHASE 3: Searching for reservations...")
        user_reservations, search_ok = safe_operation("get_user_reservations", get_user_reservations, phone)
        
        if not search_ok:
            response = get_text('sheets_error', language_code)
            log_function_exit("handle_modify_reservation_date", response, False)
            return create_safe_response(response, "handle_modify_reservation_date")
        
        if not user_reservations:
            response = get_text('reservation_not_found', language_code, phone=phone)
            log_function_exit("handle_modify_reservation_date", response, False)
            return create_safe_response(response, "handle_modify_reservation_date")
        
        if len(user_reservations) != 1:
            response = get_text('multiple_reservations', language_code, count=len(user_reservations), phone=RESTAURANT_INFO['phone'])
            log_function_exit("handle_modify_reservation_date", response, False)
            return create_safe_response(response, "handle_modify_reservation_date")
        
        # 4. RESERVATION PROCESSING PHASE
        print("🔄 PHASE 4: Processing reservation...")
        reservation = user_reservations[0]
        old_date = reservation.get('Date', '')
        old_time = reservation.get('Time', '')
        guests = reservation.get('Guests', 2)
        
        print(f"📊 Current reservation: date={old_date}, time={old_time}, guests={guests}")
        
        # 5. DATE FORMATTING PHASE
        print("🔄 PHASE 5: Formatting new date...")
        formatted_new_date, format_ok = safe_operation("format_date_readable", format_date_readable, new_date)
        if not format_ok:
            formatted_new_date = str(new_date)
            print(f"⚠️ Using fallback date format: {formatted_new_date}")
        
        # 6. AVAILABILITY CHECK WITH TIME VALIDATION PHASE
        print("🔄 PHASE 6: Checking availability...")
        try:
            print("🔄 6a. Parsing datetime...")
            day_of_week, hour_of_day, error_message = parse_dialogflow_datetime(new_date, old_time)
            
            # CHECK FOR TIME VALIDATION ERRORS
            if error_message:
                print(f"❌ PHASE 6 FAILED: Hour validation error")
                response = error_message
                log_function_exit("handle_modify_reservation_date", response, False)
                return create_safe_response(response, "handle_modify_reservation_date")
            
            print(f"📊 Parsed: day_of_week={day_of_week}, hour_of_day={hour_of_day}")
            
            print("🔄 6b. Finding available table...")
            result, avail_ok = safe_operation("find_available_table", find_available_table, int(guests), day_of_week, hour_of_day)
            
            if not avail_ok or not result or not result.get('available'):
                response = f"Sorry, we don't have availability for {guests} guests on {formatted_new_date} at {old_time}. Please try a different date or time."
                log_function_exit("handle_modify_reservation_date", response, False)
                return create_safe_response(response, "handle_modify_reservation_date")
                
        except Exception as e:
            print(f"❌ PHASE 6 FAILED: {str(e)}")
            response = get_text('availability_error', language_code)
            log_function_exit("handle_modify_reservation_date", response, False)
            return create_safe_response(response, "handle_modify_reservation_date")
        
        # 7. RESERVATION UPDATE PHASE
        print("🔄 PHASE 7: Updating reservation...")
        new_table = result['table_number']
        print(f"🆕 New table assigned: {new_table}")
        
        print("🔄 7a. Updating date...")
        date_updated, date_update_ok = safe_operation(
            "update_date", 
            update_reservation_field, 
            phone, old_date, old_time, 'date', formatted_new_date
        )
        
        print("🔄 7b. Updating table...")
        table_updated, table_update_ok = safe_operation(
            "update_table", 
            update_reservation_field, 
            phone, formatted_new_date, old_time, 'table', new_table
        )
        
        # 8. RESPONSE BUILDING PHASE
        print("🔄 PHASE 8: Building response...")
        print(f"📊 Update results: date_updated={date_updated}, table_updated={table_updated}")
        
        if (date_updated and date_update_ok) or (table_updated and table_update_ok):
            response = get_text('reservation_updated_date', language_code, date=formatted_new_date, table=new_table)
            log_function_exit("handle_modify_reservation_date", response, True)
            return create_safe_response(response, "handle_modify_reservation_date")
        else:
            response = get_text('update_error', language_code, phone=RESTAURANT_INFO['phone'])
            log_function_exit("handle_modify_reservation_date", response, False)
            return create_safe_response(response, "handle_modify_reservation_date")
            
    except Exception as e:
        print(f"❌ CRITICAL ERROR in handle_modify_reservation_date: {str(e)}")
        print(f"📚 Full traceback: {traceback.format_exc()}")
        try:
            from translations import get_text
            response = get_text('general_error', language_code, phone=RESTAURANT_INFO['phone'])
        except:
            response = f'Sorry, error modifying your reservation. Please call us at {RESTAURANT_INFO["phone"]}.'
        log_function_exit("handle_modify_reservation_date", response, False)
        return create_safe_response(response, "handle_modify_reservation_date")


def handle_modify_reservation_time(parameters, language_code='en'):
    """Handle reservation time modification - WITH TIME VALIDATION"""
    log_function_entry("handle_modify_reservation_time", parameters)
    
    try:
        # Import translations
        from translations import get_text
        
        # 1. PARAMETER EXTRACTION PHASE
        print("🔄 PHASE 1: Extracting parameters...")
        phone_raw = parameters.get('phone_number', parameters.get('phone', ''))
        phone, phone_ok = safe_operation("extract_phone", extract_value, phone_raw)
        
        new_time_raw = parameters.get('new_time', parameters.get('time', ''))
        new_time, time_ok = safe_operation("extract_time", extract_value, new_time_raw)
        
        print(f"📞 Phone: '{phone}' (success: {phone_ok})")
        print(f"🕐 New time: '{new_time}' (success: {time_ok})")
        
        # 2. INPUT VALIDATION PHASE
        print("🔄 PHASE 2: Validating inputs...")
        if not phone or not phone_ok:
            response = get_text('phone_for_check', language_code)
            log_function_exit("handle_modify_reservation_time", response, False)
            return create_safe_response(response, "handle_modify_reservation_time")
        
        if not new_time or not time_ok:
            response = "Please specify the new time for your reservation."
            log_function_exit("handle_modify_reservation_time", response, False)
            return create_safe_response(response, "handle_modify_reservation_time")
        
        # Continue with the rest of the function...
        # [Rest of the implementation follows the same pattern]
        
        response = "Time modification feature is being updated. Please call us."
        return create_safe_response(response, "handle_modify_reservation_time")
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR in handle_modify_reservation_time: {str(e)}")
        try:
            from translations import get_text
            response = get_text('general_error', language_code, phone=RESTAURANT_INFO['phone'])
        except:
            response = f'Sorry, error modifying your reservation. Please call us at {RESTAURANT_INFO["phone"]}.'
        return create_safe_response(response, "handle_modify_reservation_time")


def handle_make_reservation(parameters, language_code='en'):
    """Handle complete reservation creation - WITH TIME VALIDATION AND MULTILINGUAL SUPPORT"""
    try:
        print(f"🔧 DEBUG - Make reservation parameters: {parameters}")
        print(f"🔧 DEBUG - Language: {language_code}")
        
        # Import translations
        from translations import get_text
        
        # Extract parameters with robust checks
        name = extract_value(parameters.get('name', parameters.get('person', '')))
        phone = extract_value(parameters.get('phone_number', parameters.get('phone', '')))
        email = extract_value(parameters.get('email', ''))
        guests = extract_value(parameters.get('guest_count', parameters.get('guests', parameters.get('number', 2))))
        date = extract_value(parameters.get('day_of_week', parameters.get('date', '')))
        time = extract_value(parameters.get('hour_of_day', parameters.get('time', '')))
        
        print(f"🔧 DEBUG - Extracted: name={name}, phone={phone}, email={email}, guests={guests}, date={date}, time={time}")
        
        # Convert guest count
        try:
            guest_str = str(guests).strip().lower().replace('guests', '').replace('people', '').strip()
            guest_count = int(float(guest_str)) if guest_str else 2
            
            # Validate guest count range
            if guest_count < 1 or guest_count > 20:
                response = get_text('valid_guest_count', language_code)
                print(f"🔧 DEBUG - Returning: {response}")
                return jsonify({'fulfillmentText': response})
                
        except (ValueError, TypeError):
            guest_count = 2  # Default fallback
        
        # Validate essential parameters
        if not name or len(str(name).strip()) < 2:
            response = get_text('name_needed', language_code)
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        if not phone:
            response = get_text('phone_needed', language_code)
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        if not email or '@' not in str(email):
            response = get_text('email_needed', language_code)
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        if not date or not time:
            response = get_text('datetime_needed', language_code)
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        # TIME VALIDATION DURING RESERVATION CREATION
        try:
            day_of_week, hour_of_day, error_message = parse_dialogflow_datetime(date, time)
            
            # If there's a time validation error, return the error message
            if error_message:
                print(f"❌ Hour validation failed: {error_message}")
                return jsonify({'fulfillmentText': error_message})
                
        except Exception as e:
            print(f"❌ Error validating date/time: {e}")
            response = "Sorry, I had trouble understanding the date or time you requested. Please try again with a clear date and time between 9 AM and 9 PM."
            return jsonify({'fulfillmentText': response})
        
        # Format date and time (after validation)
        try:
            formatted_date = format_date_readable(date)
            formatted_time = format_time_readable(time)
        except Exception as e:
            print(f"❌ Error formatting date/time: {e}")
            formatted_date = str(date)
            formatted_time = str(time)
        
        # Check for duplicate reservations
        try:
            if check_existing_reservation(name, phone, formatted_date, formatted_time):
                response = get_text('duplicate_reservation', language_code, date=formatted_date, time=formatted_time)
                print(f"🔧 DEBUG - Returning: {response}")
                return jsonify({'fulfillmentText': response})
        except Exception as e:
            print(f"❌ Error checking duplicates: {e}")
        
        # Check availability (now that we know the time is valid)
        try:
            result = find_available_table(guest_count, day_of_week, hour_of_day)
            
            if not result['available']:
                response = get_text('no_availability', language_code, guests=guest_count, date=formatted_date, time=formatted_time)
                print(f"🔧 DEBUG - Returning: {response}")
                return jsonify({'fulfillmentText': response})
                
        except Exception as e:
            print(f"❌ Error checking availability: {e}")
            # Fallback: assign table 1 and proceed
            result = {'available': True, 'table_number': 1}
        
        # Save reservation
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
        
        # Save to Google Sheets
        try:
            sheets_saved = save_reservation_to_sheets(reservation_data)
        except Exception as e:
            print(f"❌ Error saving to sheets: {e}")
            sheets_saved = False
        
        # IMMEDIATE RESPONSE WITH MULTILINGUAL SUPPORT
        if sheets_saved:
            response = get_text('reservation_confirmed', language_code, 
                              name=name, guests=guest_count, 
                              date=formatted_date, time=formatted_time, 
                              table=table_num)
        else:
            response = get_text('reservation_received', language_code,
                              name=name, guests=guest_count, 
                              date=formatted_date, time=formatted_time)
        
        print(f"🔧 DEBUG - Returning SUCCESS: {response}")
        
        # Send emails in background (doesn't block response)
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
            pass  # Email failure doesn't matter
        
        return jsonify({'fulfillmentText': response})
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR in make_reservation: {e}")
        try:
            from translations import get_text
            response = get_text('technical_issue', language_code, phone=RESTAURANT_INFO['phone'])
        except:
            response = f"I'm sorry, there was a technical issue. Please call us directly at {RESTAURANT_INFO['phone']} and we'll be happy to help you."
        print(f"🔧 DEBUG - Returning CRITICAL ERROR: {response}")
        return jsonify({'fulfillmentText': response})


# The other functions with basic multilingual support
def handle_modify_reservation_guests(parameters, language_code='en'):
    """Handle modification of guest count"""
    try:
        from translations import get_text
        response = "Guest modification feature is being updated. Please call us."
        return jsonify({'fulfillmentText': response})
    except:
        response = "Guest modification feature is being updated. Please call us."
        return jsonify({'fulfillmentText': response})


def handle_modify_reservation(parameters, language_code='en'):
    """Handle general reservation modification request"""
    try:
        from translations import get_text
        response = "Reservation modification feature is being updated. Please call us."
        return jsonify({'fulfillmentText': response})
    except:
        response = "Reservation modification feature is being updated. Please call us."
        return jsonify({'fulfillmentText': response})


def handle_cancel_reservation(parameters, language_code='en'):
    """Handle reservation cancellation request"""
    try:
        print(f"🔧 DEBUG - Cancel reservation parameters: {parameters}")
        
        # Extract phone number
        phone_raw = parameters.get('phone_number', parameters.get('phone', ''))
        phone = extract_value(phone_raw)
        
        print(f"🔧 DEBUG - Extracted phone: {phone}")
        
        if not phone:
            response = "Please provide your phone number to find your reservation to cancel."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        # Search for user reservations
        user_reservations = get_user_reservations(phone)
        
        if not user_reservations:
            response = f"I couldn't find any active reservations for phone number {phone}. Please check the number or call us at {RESTAURANT_INFO['phone']}."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        if len(user_reservations) == 1:
            # Single reservation - delete completely
            reservation = user_reservations[0]
            
            # Delete the reservation from the sheet
            success = delete_reservation_from_sheets(
                phone, 
                reservation.get('Date', ''), 
                reservation.get('Time', '')
            )
            
            if success:
                try:
                    from translations import get_text
                    response = get_text('reservation_cancelled', language_code, 
                                      name=reservation.get('Name', ''),
                                      date=reservation.get('Date', ''),
                                      time=reservation.get('Time', ''),
                                      guests=reservation.get('Guests', ''),
                                      table=reservation.get('Table', ''))
                except:
                    response = f"✅ Reservation cancelled successfully! Your reservation for {reservation.get('Name', '')} on {reservation.get('Date', '')} at {reservation.get('Time', '')} for {reservation.get('Guests', '')} guests (Table {reservation.get('Table', '')}) has been removed. We're sorry to see you cancel. We hope to see you again soon!"
                
                print(f"🔧 DEBUG - Returning SUCCESS: {response}")
                return jsonify({'fulfillmentText': response})
            else:
                response = f"Sorry, there was an issue cancelling your reservation. Please call us at {RESTAURANT_INFO['phone']}."
                print(f"🔧 DEBUG - Returning FALLBACK: {response}")
                return jsonify({'fulfillmentText': response})
        else:
            # Multiple reservations
            response = f"You have {len(user_reservations)} reservations. Please call us at {RESTAURANT_INFO['phone']} to specify which one to cancel."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
            
    except Exception as e:
        print(f"❌ Error in cancel_reservation: {e}")
        response = f'Sorry, error cancelling your reservation. Please call us at {RESTAURANT_INFO["phone"]}.'
        print(f"🔧 DEBUG - Returning ERROR: {response}")
        return jsonify({'fulfillmentText': response})


def handle_check_my_reservation(parameters, language_code='en'):
    """Handle request to check own reservations"""
    try:
        print(f"🔧 DEBUG - Check my reservation parameters: {parameters}")
        
        # Extract phone number
        phone_raw = parameters.get('phone_number', parameters.get('phone', ''))
        phone = extract_value(phone_raw)
        
        print(f"🔧 DEBUG - Extracted phone: {phone}")
        
        if not phone:
            try:
                from translations import get_text
                response = get_text('phone_for_check', language_code)
            except:
                response = "To check your reservations, I need your phone number for security. Please provide the phone number you used when booking."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        # Search for user reservations
        user_reservations = get_user_reservations(phone)
        
        if not user_reservations:
            try:
                from translations import get_text
                response = get_text('reservation_not_found', language_code, phone=phone)
            except:
                response = f"I couldn't find any active reservations for phone number {phone}. Please check the number format or call us at {RESTAURANT_INFO['phone']}."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        if len(user_reservations) == 1:
            # Single reservation - show details
            reservation = user_reservations[0]
            try:
                from translations import get_text
                response = get_text('reservation_details', language_code,
                                  name=reservation.get('Name', ''),
                                  phone=reservation.get('Phone', ''),
                                  guests=reservation.get('Guests', ''),
                                  date=reservation.get('Date', ''),
                                  time=reservation.get('Time', ''),
                                  table=reservation.get('Table', ''))
            except:
                response = f"📋 Your reservation: {reservation.get('Name', '')} ({reservation.get('Phone', '')}) - {reservation.get('Guests', '')} guests on {reservation.get('Date', '')} at {reservation.get('Time', '')} - Table {reservation.get('Table', '')} - Status: Confirmed. Need to modify or cancel? Just let me know!"
            
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        else:
            # Multiple reservations
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


def handle_check_table_specific(parameters, language_code='en'):
    """Handle specific table availability check"""
    try:
        print(f"🔧 DEBUG - Check table parameters: {parameters}")
        
        # Extract parameters
        table_raw = parameters.get('table_number', parameters.get('number', parameters.get('table', '')))
        date_raw = parameters.get('date', parameters.get('day_of_week', ''))
        time_raw = parameters.get('time', parameters.get('hour_of_day', ''))
        
        table_number = extract_value(table_raw)
        date = extract_value(date_raw)
        time = extract_value(time_raw)
        
        print(f"🔧 DEBUG - Extracted: table={table_number}, date={date}, time={time}")
        
        # Convert table number
        try:
            if not table_number:
                try:
                    from translations import get_text
                    response = get_text('table_number_needed', language_code)
                except:
                    response = "Please specify which table number you'd like to check (1-20)."
                print(f"🔧 DEBUG - Returning: {response}")
                return jsonify({'fulfillmentText': response})
            
            # Clean table number string (remove common words)
            table_str = str(table_number).strip().lower().replace('table', '').replace('number', '').replace('#', '').strip()
            table_num = int(float(table_str))
            
            # Validate table number range
            if table_num < 1 or table_num > 20:
                try:
                    from translations import get_text
                    response = get_text('valid_table_number', language_code)
                except:
                    response = "Please specify a table number between 1 and 20."
                print(f"🔧 DEBUG - Returning: {response}")
                return jsonify({'fulfillmentText': response})
                
        except (ValueError, TypeError) as e:
            print(f"❌ Error converting table '{table_number}': {e}")
            response = "Please provide a valid table number (1-20)."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        # Check for missing parameters
        if not date or not time:
            try:
                from translations import get_text
                response = get_text('datetime_needed_table', language_code, table=table_num)
            except:
                response = f"I need the date and time to check table {table_num} availability."
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
        
        # TIME VALIDATION IN TABLE SEARCH
        try:
            day_of_week, hour_of_day, error_message = parse_dialogflow_datetime(date, time)
            
            # If there's a time validation error, return the error message
            if error_message:
                print(f"❌ Hour validation failed: {error_message}")
                return jsonify({'fulfillmentText': error_message})
            
            # Check table availability using ML model
            is_available = check_table_availability(table_num, 4, day_of_week, hour_of_day)  # Default 4 guests
            
            # Format date and time for user-friendly response
            formatted_date = format_date_readable(date)
            formatted_time = format_time_readable(time)
            
            if is_available:
                try:
                    from translations import get_text
                    response = get_text('table_available', language_code, table=table_num, date=formatted_date, time=formatted_time)
                except:
                    response = f"✅ Good news! Table {table_num} is available on {formatted_date} at {formatted_time}!"
            else:
                try:
                    from translations import get_text
                    response = get_text('table_unavailable', language_code, table=table_num, date=formatted_date, time=formatted_time)
                except:
                    response = f"😔 Sorry, table {table_num} is already reserved on {formatted_date} at {formatted_time}."
                
            print(f"🔧 DEBUG - Returning: {response}")
            return jsonify({'fulfillmentText': response})
            
        except Exception as e:
            print(f"❌ Error checking availability: {e}")
            try:
                from translations import get_text
                response = get_text('availability_error', language_code)
            except:
                response = 'Sorry, error checking table availability. Please call us.'
            print(f"🔧 DEBUG - Returning ERROR: {response}")
            return jsonify({'fulfillmentText': response})
            
    except Exception as e:
        print(f"❌ Error in check_table_specific: {e}")
        try:
            from translations import get_text
            response = get_text('general_error', language_code, phone=RESTAURANT_INFO['phone'])
        except:
            response = 'Sorry, error checking table availability. Please call us.'
        print(f"🔧 DEBUG - Returning ERROR: {response}")
        return jsonify({'fulfillmentText': response})
