"""
Handlers for restaurant reservation management
"""
from flask import jsonify, request, Response
import re
import traceback
import time
import threading
import json

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
                return create_safe_response(response, "handle_make_reservation")
                
        except (ValueError, TypeError):
            guest_count = 2  # Default fallback
        
        # Validate essential parameters
        if not name or len(str(name).strip()) < 2:
            response = get_text('name_needed', language_code)
            return create_safe_response(response, "handle_make_reservation")
        
        if not phone:
            response = get_text('phone_needed', language_code)
            return create_safe_response(response, "handle_make_reservation")
        
        if not email or '@' not in str(email):
            response = get_text('email_needed', language_code)
            return create_safe_response(response, "handle_make_reservation")
        
        if not date or not time:
            response = get_text('datetime_needed', language_code)
            return create_safe_response(response, "handle_make_reservation")
        
        # TIME VALIDATION DURING RESERVATION CREATION
        try:
            day_of_week, hour_of_day, error_message = parse_dialogflow_datetime(date, time)
            
            # If there's a time validation error, return the error message
            if error_message:
                return create_safe_response(error_message, "handle_make_reservation")
                
        except Exception as e:
            response = "Sorry, I had trouble understanding the date or time you requested. Please try again with a clear date and time between 9 AM and 9 PM."
            return create_safe_response(response, "handle_make_reservation")
        
        # Format date and time (after validation)
        try:
            formatted_date = format_date_readable(date)
            formatted_time = format_time_readable(time)
        except Exception as e:
            formatted_date = str(date)
            formatted_time = str(time)
        
        # Check for duplicate reservations
        try:
            if check_existing_reservation(name, phone, formatted_date, formatted_time):
                response = get_text('duplicate_reservation', language_code, date=formatted_date, time=formatted_time)
                return create_safe_response(response, "handle_make_reservation")
        except Exception as e:
            print(f"❌ Error checking duplicates: {e}")
        
        # Check availability (now that we know the time is valid)
        try:
            result = find_available_table(guest_count, day_of_week, hour_of_day)
            
            if not result['available']:
                response = get_text('no_availability', language_code, guests=guest_count, date=formatted_date, time=formatted_time)
                return create_safe_response(response, "handle_make_reservation")
                
        except Exception as e:
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
        
        # Send emails in background (doesn't block response)
        try:
            import threading
            def send_emails_background():
                try:
                    send_confirmation_email(reservation_data)
                    send_admin_notification(reservation_data)
                except:
                    pass
            
            email_thread = threading.Thread(target=send_emails_background)
            email_thread.daemon = True
            email_thread.start()
        except:
            pass
        
        return create_safe_response(response, "handle_make_reservation")
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR in make_reservation: {e}")
        try:
            from translations import get_text
            response = get_text('technical_issue', language_code, phone=RESTAURANT_INFO['phone'])
        except:
            response = f"I'm sorry, there was a technical issue. Please call us directly at {RESTAURANT_INFO['phone']} and we'll be happy to help you."
        return create_safe_response(response, "handle_make_reservation")


def handle_cancel_reservation(parameters, language_code='en'):
    """Handle reservation cancellation request"""
    try:
        # Extract phone number
        phone_raw = parameters.get('phone_number', parameters.get('phone', ''))
        phone = extract_value(phone_raw)
        
        if not phone:
            response = "Please provide your phone number to find your reservation to cancel."
            return create_safe_response(response, "handle_cancel_reservation")
        
        # Search for user reservations
        user_reservations = get_user_reservations(phone)
        
        if not user_reservations:
            response = f"I couldn't find any active reservations for phone number {phone}. Please check the number or call us at {RESTAURANT_INFO['phone']}."
            return create_safe_response(response, "handle_cancel_reservation")
        
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
                
                return create_safe_response(response, "handle_cancel_reservation")
            else:
                response = f"Sorry, there was an issue cancelling your reservation. Please call us at {RESTAURANT_INFO['phone']}."
                return create_safe_response(response, "handle_cancel_reservation")
        else:
            # Multiple reservations
            response = f"You have {len(user_reservations)} reservations. Please call us at {RESTAURANT_INFO['phone']} to specify which one to cancel."
            return create_safe_response(response, "handle_cancel_reservation")
            
    except Exception as e:
        response = f'Sorry, error cancelling your reservation. Please call us at {RESTAURANT_INFO["phone"]}.'
        return create_safe_response(response, "handle_cancel_reservation")


def handle_check_my_reservation(parameters, language_code='en'):
    """Handle request to check own reservations"""
    try:
        # Extract phone number
        phone_raw = parameters.get('phone_number', parameters.get('phone', ''))
        phone = extract_value(phone_raw)
        
        if not phone:
            try:
                from translations import get_text
                response = get_text('phone_for_check', language_code)
            except:
                response = "To check your reservations, I need your phone number for security. Please provide the phone number you used when booking."
            return create_safe_response(response, "handle_check_my_reservation")
        
        # Search for user reservations
        user_reservations = get_user_reservations(phone)
        
        if not user_reservations:
            try:
                from translations import get_text
                response = get_text('reservation_not_found', language_code, phone=phone)
            except:
                response = f"I couldn't find any active reservations for phone number {phone}. Please check the number format or call us at {RESTAURANT_INFO['phone']}."
            return create_safe_response(response, "handle_check_my_reservation")
        
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
            
            return create_safe_response(response, "handle_check_my_reservation")
        else:
            # Multiple reservations
            reservation_details = []
            for i, res in enumerate(user_reservations, 1):
                reservation_details.append(f"{i}. {res.get('Date', '')} at {res.get('Time', '')} - {res.get('Guests', '')} guests (Table {res.get('Table', '')})")
            
            response = f"📋 You have {len(user_reservations)} active reservations: " + "; ".join(reservation_details) + ". Need to modify or cancel any reservation? Just let me know!"
            return create_safe_response(response, "handle_check_my_reservation")
            
    except Exception as e:
        response = f'Sorry, error checking your reservations. Please call us at {RESTAURANT_INFO["phone"]}.'
        return create_safe_response(response, "handle_check_my_reservation")


def handle_check_table_specific(parameters, language_code='en'):
    """Handle specific table availability check"""
    try:
        # Extract parameters
        table_raw = parameters.get('table_number', parameters.get('number', parameters.get('table', '')))
        date_raw = parameters.get('date', parameters.get('day_of_week', ''))
        time_raw = parameters.get('time', parameters.get('hour_of_day', ''))
        
        table_number = extract_value(table_raw)
        date = extract_value(date_raw)
        time = extract_value(time_raw)
        
        # Convert table number
        try:
            if not table_number:
                try:
                    from translations import get_text
                    response = get_text('table_number_needed', language_code)
                except:
                    response = "Please specify which table number you'd like to check (1-20)."
                return create_safe_response(response, "handle_check_table_specific")
            
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
                return create_safe_response(response, "handle_check_table_specific")
                
        except (ValueError, TypeError) as e:
            response = "Please provide a valid table number (1-20)."
            return create_safe_response(response, "handle_check_table_specific")
        
        # Check for missing parameters
        if not date or not time:
            try:
                from translations import get_text
                response = get_text('datetime_needed_table', language_code, table=table_num)
            except:
                response = f"I need the date and time to check table {table_num} availability."
            return create_safe_response(response, "handle_check_table_specific")
        
        # TIME VALIDATION IN TABLE SEARCH
        try:
            day_of_week, hour_of_day, error_message = parse_dialogflow_datetime(date, time)
            
            # If there's a time validation error, return the error message
            if error_message:
                return create_safe_response(error_message, "handle_check_table_specific")
            
            # Check table availability using ML model
            is_available = check_table_availability(table_num, 4, day_of_week, hour_of_day)
            
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
                
            return create_safe_response(response, "handle_check_table_specific")
            
        except Exception as e:
            try:
                from translations import get_text
                response = get_text('availability_error', language_code)
            except:
                response = 'Sorry, error checking table availability. Please call us.'
            return create_safe_response(response, "handle_check_table_specific")
            
    except Exception as e:
        try:
            from translations import get_text
            response = get_text('general_error', language_code, phone=RESTAURANT_INFO['phone'])
        except:
            response = 'Sorry, error checking table availability. Please call us.'
        return create_safe_response(response, "handle_check_table_specific")


# Simple handlers for modification functions
def handle_modify_reservation_date(parameters, language_code='en'):
    """Handle reservation date modification"""
    try:
        from translations import get_text
        response = get_text('update_error', language_code, phone=RESTAURANT_INFO['phone'])
        return create_safe_response(response, "handle_modify_reservation_date")
    except:
        response = f"Date modification feature is being updated. Please call us at {RESTAURANT_INFO['phone']}."
        return create_safe_response(response, "handle_modify_reservation_date")


def handle_modify_reservation_time(parameters, language_code='en'):
    """Handle reservation time modification"""
    try:
        from translations import get_text
        response = get_text('update_error', language_code, phone=RESTAURANT_INFO['phone'])
        return create_safe_response(response, "handle_modify_reservation_time")
    except:
        response = f"Time modification feature is being updated. Please call us at {RESTAURANT_INFO['phone']}."
        return create_safe_response(response, "handle_modify_reservation_time")


def handle_modify_reservation_guests(parameters, language_code='en'):
    """Handle modification of guest count"""
    try:
        from translations import get_text
        response = get_text('update_error', language_code, phone=RESTAURANT_INFO['phone'])
        return create_safe_response(response, "handle_modify_reservation_guests")
    except:
        response = f"Guest modification feature is being updated. Please call us at {RESTAURANT_INFO['phone']}."
        return create_safe_response(response, "handle_modify_reservation_guests")


def handle_modify_reservation(parameters, language_code='en'):
    """Handle general reservation modification request"""
    try:
        from translations import get_text
        response = get_text('update_error', language_code, phone=RESTAURANT_INFO['phone'])
        return create_safe_response(response, "handle_modify_reservation")
    except:
        response = f"Reservation modification feature is being updated. Please call us at {RESTAURANT_INFO['phone']}."
        return create_safe_response(response, "handle_modify_reservation")
