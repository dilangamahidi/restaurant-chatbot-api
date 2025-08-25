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
    """Handle menu display - Multiple separate messages for better organization"""
    try:
        from translations import get_text
        
        # Extract menu category from user parameters
        menu_category = parameters.get('menu-category', '').lower() if parameters else ''
        
        # If user requested a specific menu category, show only that category
        if menu_category and menu_category in MENU:
            items = MENU[menu_category]
            response_text = f"🍽️ {menu_category.title()} Menu:\n\n" + "\n".join([f"{i}. {item}" for i, item in enumerate(items, 1)])
            return create_utf8_response({'fulfillmentText': response_text})
        else:
            # Show menu header first
            menu_header = get_text('menu_header', language_code, restaurant=RESTAURANT_INFO['name'])
            breakfast_header = get_text('breakfast', language_code)
            lunch_header = get_text('lunch', language_code)
            dinner_header = get_text('dinner', language_code)
            beverages_header = get_text('beverages', language_code)
            
            # Create multiple separate messages
            messages = [
                menu_header,
                f"{breakfast_header}:\n1. {MENU['breakfast'][0]}\n2. {MENU['breakfast'][1]}\n3. {MENU['breakfast'][2]}\n4. {MENU['breakfast'][3]}",
                f"{lunch_header}:\n1. {MENU['lunch'][0]}\n2. {MENU['lunch'][1]}\n3. {MENU['lunch'][2]}\n4. {MENU['lunch'][3]}",
                f"{dinner_header}:\n1. {MENU['dinner'][0]}\n2. {MENU['dinner'][1]}\n3. {MENU['dinner'][2]}\n4. {MENU['dinner'][3]}",
                f"{beverages_header}:\n• {MENU['beverages'][0]}\n• {MENU['beverages'][1]}\n• {MENU['beverages'][2]}\n• {MENU['beverages'][3]}"
            ]
            
            # Join messages with double newlines to create visual separation
            complete_menu = "\n\n".join(messages)
            return create_utf8_response({'fulfillmentText': complete_menu})
    except Exception as e:
        try:
            print(f"Error in handle_show_menu: {e}")
        except:
            print(f"Error in handle_show_menu: {str(e)}")
        # Fallback with multiple separate messages
        messages = [
            f"🍽️ {RESTAURANT_INFO['name']} Menu",
            "☀️ Breakfast:\n1. String Hoppers with Curry\n2. Milk Rice (Kiribath)\n3. Coconut Roti with Sambol\n4. Ceylon Tea",
            "🍛 Lunch:\n1. Rice and Curry\n2. Kottu Roti\n3. Fried Rice\n4. Hoppers with Egg",
            "🌅 Dinner:\n1. Fish Curry\n2. Chicken Curry\n3. Seafood Platter\n4. Vegetarian Curry",
            "🥤 Beverages:\n• King Coconut\n• Ceylon Tea\n• Fresh Juices\n• Local Beer"
        ]
        fallback_menu = "\n\n".join(messages)
        return create_utf8_response({'fulfillmentText': fallback_menu})


def handle_opening_hours(language_code='en'):
    """Handle opening hours display with multilingual support - Multiple separate messages"""
    try:
        from translations import get_text
        
        # Create multiple separate messages
        header = get_text('opening_hours_header', language_code, restaurant=RESTAURANT_INFO['name'])
        weekday_hours = get_text('weekday_hours', language_code)
        sunday_hours = get_text('sunday_hours', language_code)
        
        messages = [
            header,
            f"🗓️ {weekday_hours}",
            f"🗓️ {sunday_hours}"
        ]
        
        complete_hours = "\n\n".join(messages)
        return create_utf8_response({'fulfillmentText': complete_hours})
    except Exception as e:
        try:
            print(f"Error in handle_opening_hours: {e}")
        except:
            print(f"Error in handle_opening_hours: {str(e)}")
        # Fallback with multiple separate messages
        messages = [
            f"🕐 {RESTAURANT_INFO['name']} Opening Hours",
            "🗓️ Monday - Saturday:\n⏰ 09:00 AM - 09:00 PM",
            "🗓️ Sunday:\n⏰ 10:00 AM - 08:00 PM"
        ]
        response_text = "\n\n".join(messages)
        return create_utf8_response({'fulfillmentText': response_text})


def handle_restaurant_info(language_code='en'):
    """Handle restaurant information display with multilingual support - Multiple separate messages"""
    try:
        from translations import get_text
        
        # Create multiple separate messages
        header = get_text('restaurant_info_header', language_code, restaurant=RESTAURANT_INFO['name'])
        address_label = get_text('address_label', language_code, address=RESTAURANT_INFO['address'])
        phone_label = get_text('phone_label', language_code, phone=RESTAURANT_INFO['phone'])
        email_label = get_text('email_label', language_code, email=RESTAURANT_INFO['email'])
        hours_summary = get_text('hours_summary', language_code)
        
        messages = [
            header,
            f"📖 Description:\n{RESTAURANT_INFO['description']}",
            f"🏠 {address_label}",
            f"📞 {phone_label}",
            f"📧 {email_label}",
            f"🕐 Hours:\n{hours_summary}"
        ]
        
        complete_info = "\n\n".join(messages)
        return create_utf8_response({'fulfillmentText': complete_info})
    except Exception as e:
        try:
            print(f"Error in handle_restaurant_info: {e}")
        except:
            print(f"Error in handle_restaurant_info: {str(e)}")
        # Fallback with multiple separate messages
        messages = [
            f"🍽️ {RESTAURANT_INFO['name']}",
            f"📖 Description:\n{RESTAURANT_INFO['description']}",
            f"🏠 Address:\n{RESTAURANT_INFO['address']}",
            f"📞 Phone:\n{RESTAURANT_INFO['phone']}",
            f"📧 Email:\n{RESTAURANT_INFO['email']}",
            "🕐 Hours:\n⏰ Mon-Sat: 9AM-9PM\n⏰ Sun: 10AM-8PM"
        ]
        response_text = "\n\n".join(messages)
        return create_utf8_response({'fulfillmentText': response_text})


def handle_contact_human(language_code='en'):
    """Handle human contact request with multilingual support - Multiple separate messages"""
    try:
        from translations import get_text
        
        # Create multiple separate messages
        contact_header = get_text('contact_staff', language_code)
        phone_label = get_text('phone_label', language_code, phone=RESTAURANT_INFO['phone'])
        email_label = get_text('email_label', language_code, email=RESTAURANT_INFO['email'])
        
        messages = [
            contact_header,
            f"📞 {phone_label}",
            f"📧 {email_label}"
        ]
        
        complete_contact = "\n\n".join(messages)
        return create_utf8_response({'fulfillmentText': complete_contact})
    except Exception as e:
        try:
            print(f"Error in handle_contact_human: {e}")
        except:
            print(f"Error in handle_contact_human: {str(e)}")
        # Fallback with multiple separate messages
        messages = [
            "👨‍💼 Contact our staff",
            f"📞 Phone:\n{RESTAURANT_INFO['phone']}",
            f"📧 Email:\n{RESTAURANT_INFO['email']}"
        ]
        response_text = "\n\n".join(messages)
        return create_utf8_response({'fulfillmentText': response_text})


def handle_restaurant_location(language_code='en'):
    """Handle restaurant location request with multilingual support - Multiple separate messages"""
    try:
        from translations import get_text
        
        # Create multiple separate messages
        location_header = get_text('location_header', language_code, restaurant=RESTAURANT_INFO['name'])
        location_address = get_text('location_address', language_code, address=RESTAURANT_INFO['address'])
        
        messages = [
            location_header,
            f"🏠 {location_address}"
        ]
        
        complete_location = "\n\n".join(messages)
        return create_utf8_response({'fulfillmentText': complete_location})
    except Exception as e:
        try:
            print(f"Error in handle_restaurant_location: {e}")
        except:
            print(f"Error in handle_restaurant_location: {str(e)}")
        # Fallback with multiple separate messages
        messages = [
            f"📍 {RESTAURANT_INFO['name']} Location",
            f"🏠 Address:\n{RESTAURANT_INFO['address']}"
        ]
        response_text = "\n\n".join(messages)
        return create_utf8_response({'fulfillmentText': response_text})
