"""
Handlers for restaurant information management
"""
import json
from flask import Response

# Import from our modules
from config import RESTAURANT_INFO, MENU

def create_utf8_response(data):
    """Create UTF-8 JSON response"""
    try:
        json_string = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        return Response(
            json_string,
            content_type='application/json; charset=utf-8',
            status=200
        )
    except Exception as e:
        try:
            print(f"Error creating UTF-8 response: {e}")
        except:
            print(f"Error creating UTF-8 response: {str(e)}")
        # Fallback
        fallback = json.dumps({'fulfillmentText': 'Sorry, there was an error.'}, ensure_ascii=False)
        return Response(fallback, content_type='application/json; charset=utf-8')
    
def handle_show_menu(parameters, language_code='en'):
    """Handle menu display - Single comprehensive message with all menu items"""
    try:
        from translations import get_text
        
        # Extract menu category from user parameters
        menu_category = parameters.get('menu-category', '').lower() if parameters else ''
        
        # If user requested a specific menu category, show only that category
        if menu_category and menu_category in MENU:
            items = MENU[menu_category]
            # Format single category response with numbered items
            response_text = f"🍽️ {menu_category.title()} Menu:\n\n" + "\n".join([f"{i}. {item}" for i, item in enumerate(items, 1)])
            return create_utf8_response({'fulfillmentText': response_text})
        else:
            # Show complete menu in a single comprehensive message
            menu_header = get_text('menu_header', language_code, restaurant=RESTAURANT_INFO['name'])
            breakfast_header = get_text('breakfast', language_code)
            lunch_header = get_text('lunch', language_code)
            dinner_header = get_text('dinner', language_code)
            beverages_header = get_text('beverages', language_code)
            
            # Build complete menu text
            complete_menu = f"""{menu_header}

{breakfast_header}
• {MENU['breakfast'][0]}
• {MENU['breakfast'][1]}
• {MENU['breakfast'][2]}
• {MENU['breakfast'][3]}

{lunch_header}
• {MENU['lunch'][0]}
• {MENU['lunch'][1]}
• {MENU['lunch'][2]}
• {MENU['lunch'][3]}

{dinner_header}
• {MENU['dinner'][0]}
• {MENU['dinner'][1]}
• {MENU['dinner'][2]}
• {MENU['dinner'][3]}

{beverages_header}
• {MENU['beverages'][0]}
• {MENU['beverages'][1]}
• {MENU['beverages'][2]}
• {MENU['beverages'][3]}"""
            
            return create_utf8_response({'fulfillmentText': complete_menu})
    except Exception as e:
        try:
            print(f"Error in handle_show_menu: {e}")
        except:
            print(f"Error in handle_show_menu: {str(e)}")
        # Fallback with actual menu items
        fallback_menu = f"""🍽️ {RESTAURANT_INFO['name']} Menu:

☀️ BREAKFAST:
• String Hoppers with Curry
• Milk Rice (Kiribath)
• Coconut Roti with Sambol
• Ceylon Tea

🍛 LUNCH:
• Rice and Curry
• Kottu Roti
• Fried Rice
• Hoppers with Egg

🌅 DINNER:
• Fish Curry
• Chicken Curry
• Seafood Platter
• Vegetarian Curry

🥤 BEVERAGES:
• King Coconut
• Ceylon Tea
• Fresh Juices
• Local Beer"""
        return create_utf8_response({'fulfillmentText': fallback_menu})


def handle_opening_hours(language_code='en'):
    """Handle opening hours display with multilingual support - Single comprehensive message"""
    try:
        from translations import get_text
        
        # Create single comprehensive response
        header = get_text('opening_hours_header', language_code, restaurant=RESTAURANT_INFO['name'])
        weekday_hours = get_text('weekday_hours', language_code)
        sunday_hours = get_text('sunday_hours', language_code)
        
        complete_hours = f"""{header}

{weekday_hours}

{sunday_hours}"""
        
        return create_utf8_response({'fulfillmentText': complete_hours})
    except Exception as e:
        try:
            print(f"Error in handle_opening_hours: {e}")
        except:
            print(f"Error in handle_opening_hours: {str(e)}")
        # Fallback to English
        response_text = f"""🕐 {RESTAURANT_INFO['name']} Opening Hours:

📅 Monday - Saturday:
09:00 AM - 09:00 PM

📅 Sunday:
10:00 AM - 08:00 PM"""
        return create_utf8_response({'fulfillmentText': response_text})


def handle_restaurant_info(language_code='en'):
    """Handle restaurant information display with multilingual support - Single comprehensive message"""
    try:
        from translations import get_text
        
        # Create single comprehensive restaurant information
        header = get_text('restaurant_info_header', language_code, restaurant=RESTAURANT_INFO['name'])
        address_label = get_text('address_label', language_code, address=RESTAURANT_INFO['address'])
        phone_label = get_text('phone_label', language_code, phone=RESTAURANT_INFO['phone'])
        email_label = get_text('email_label', language_code, email=RESTAURANT_INFO['email'])
        hours_summary = get_text('hours_summary', language_code)
        
        complete_info = f"""{header}

{RESTAURANT_INFO['description']}

{address_label}

{phone_label}

{email_label}

{hours_summary}"""
        
        return create_utf8_response({'fulfillmentText': complete_info})
    except Exception as e:
        try:
            print(f"Error in handle_restaurant_info: {e}")
        except:
            print(f"Error in handle_restaurant_info: {str(e)}")
        # Fallback to English
        response_text = f"""🍽️ {RESTAURANT_INFO['name']}

{RESTAURANT_INFO['description']}

📍 Address:
{RESTAURANT_INFO['address']}

📞 Phone:
{RESTAURANT_INFO['phone']}

📧 Email:
{RESTAURANT_INFO['email']}

🕐 Hours:
Mon-Sat 9AM-9PM
Sun 10AM-8PM"""
        return create_utf8_response({'fulfillmentText': response_text})


def handle_contact_human(language_code='en'):
    """Handle human contact request with multilingual support - Single comprehensive message"""
    try:
        from translations import get_text
        
        # Provide comprehensive contact information in a single message
        contact_header = get_text('contact_staff', language_code)
        phone_label = get_text('phone_label', language_code, phone=RESTAURANT_INFO['phone'])
        email_label = get_text('email_label', language_code, email=RESTAURANT_INFO['email'])
        
        complete_contact = f"""{contact_header}

{phone_label}

{email_label}"""
        
        return create_utf8_response({'fulfillmentText': complete_contact})
    except Exception as e:
        try:
            print(f"Error in handle_contact_human: {e}")
        except:
            print(f"Error in handle_contact_human: {str(e)}")
        # Fallback to English
        response_text = f"""👨‍💼 Contact our staff:

📞 Phone:
{RESTAURANT_INFO['phone']}

📧 Email:
{RESTAURANT_INFO['email']}"""
        return create_utf8_response({'fulfillmentText': response_text})


def handle_restaurant_location(language_code='en'):
    """Handle restaurant location request with multilingual support - Single comprehensive message"""
    try:
        from translations import get_text
        
        # Provide comprehensive location information in a single message
        location_header = get_text('location_header', language_code, restaurant=RESTAURANT_INFO['name'])
        location_address = get_text('location_address', language_code, address=RESTAURANT_INFO['address'])
        
        complete_location = f"""{location_header}

{location_address}"""
        
        return create_utf8_response({'fulfillmentText': complete_location})
    except Exception as e:
        try:
            print(f"Error in handle_restaurant_location: {e}")
        except:
            print(f"Error in handle_restaurant_location: {str(e)}")
        # Fallback to English
        response_text = f"""📍 {RESTAURANT_INFO['name']} Location:

🏠 Address:
{RESTAURANT_INFO['address']}"""
        return create_utf8_response({'fulfillmentText': response_text})
