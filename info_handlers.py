"""
Handlers for restaurant information management
"""
from flask import jsonify

# Import from our modules
from config import RESTAURANT_INFO, MENU


def handle_show_menu(parameters, language_code='en'):
    """Handle menu display - MULTIPLE MESSAGES with multilingual support"""
    try:
        from translations import get_text
        
        # Extract menu category from user parameters
        menu_category = parameters.get('menu-category', '').lower() if parameters else ''
        
        # If user requested a specific menu category, show only that category
        if menu_category and menu_category in MENU:
            items = MENU[menu_category]
            # Format single category response with numbered items
            response_text = f"🍽️ {menu_category.title()} Menu:\n\n" + "\n".join([f"{i}. {item}" for i, item in enumerate(items, 1)])
            return jsonify({'fulfillmentText': response_text})
        else:
            # Show complete menu using multiple messages for better readability
            rich_response = {
                # Main fulfillment text (fallback)
                "fulfillmentText": get_text('menu_header', language_code, restaurant=RESTAURANT_INFO['name']),
                # Rich response with multiple message bubbles
                "fulfillmentMessages": [
                    {
                        # Header message with restaurant name
                        "text": {
                            "text": [get_text('menu_header', language_code, restaurant=RESTAURANT_INFO['name'])]
                        }
                    },
                    {
                        # Breakfast menu section
                        "text": {
                            "text": [get_text('breakfast', language_code) + "\n" + "\n".join([f"• {item}" for item in MENU['breakfast']])]
                        }
                    },
                    {
                        # Lunch menu section
                        "text": {
                            "text": [get_text('lunch', language_code) + "\n" + "\n".join([f"• {item}" for item in MENU['lunch']])]
                        }
                    },
                    {
                        # Dinner menu section
                        "text": {
                            "text": [get_text('dinner', language_code) + "\n" + "\n".join([f"• {item}" for item in MENU['dinner']])]
                        }
                    },
                    {
                        # Beverages section
                        "text": {
                            "text": [get_text('beverages', language_code) + "\n" + "\n".join([f"• {item}" for item in MENU['beverages']])]
                        }
                    },
                ]
            }
            return jsonify(rich_response)
    except:
        # Fallback to English
        response_text = f"🍽️ {RESTAURANT_INFO['name']} Menu:"
        return jsonify({'fulfillmentText': response_text})


def handle_opening_hours(language_code='en'):
    """Handle opening hours display with multilingual support"""
    try:
        from translations import get_text
        
        # Create structured response with separate messages
        rich_response = {
            # Fallback text
            "fulfillmentText": get_text('opening_hours_header', language_code, restaurant=RESTAURANT_INFO['name']),
            # Rich messages
            "fulfillmentMessages": [
                {
                    # Header message
                    "text": {
                        "text": [get_text('opening_hours_header', language_code, restaurant=RESTAURANT_INFO['name'])]
                    }
                },
                {
                    # Weekday hours
                    "text": {
                        "text": [get_text('weekday_hours', language_code)]
                    }
                },
                {
                    # Sunday hours
                    "text": {
                        "text": [get_text('sunday_hours', language_code)]
                    }
                },
            ]
        }
        return jsonify(rich_response)
    except:
        # Fallback to English
        response_text = f"🕐 {RESTAURANT_INFO['name']} Opening Hours:\nMonday - Saturday: 09:00 AM - 09:00 PM\nSunday: 10:00 AM - 08:00 PM"
        return jsonify({'fulfillmentText': response_text})


def handle_restaurant_info(language_code='en'):
    """Handle restaurant information display with multilingual support"""
    try:
        from translations import get_text
        
        # Create detailed restaurant information using multiple message bubbles
        rich_response = {
            # Simple fallback text
            "fulfillmentText": get_text('restaurant_info_header', language_code, restaurant=RESTAURANT_INFO['name']),
            # Detailed rich response
            "fulfillmentMessages": [
                {
                    # Restaurant name header
                    "text": {
                        "text": [get_text('restaurant_info_header', language_code, restaurant=RESTAURANT_INFO['name'])]
                    }
                },
                {
                    # Restaurant description
                    "text": {
                        "text": [f"{RESTAURANT_INFO['description']}"]
                    }
                },
                {
                    # Physical address
                    "text": {
                        "text": [get_text('address_label', language_code, address=RESTAURANT_INFO['address'])]
                    }
                },
                {
                    # Phone contact
                    "text": {
                        "text": [get_text('phone_label', language_code, phone=RESTAURANT_INFO['phone'])]
                    }
                },
                {
                    # Email contact
                    "text": {
                        "text": [get_text('email_label', language_code, email=RESTAURANT_INFO['email'])]
                    }
                },
                {
                    # Operating hours summary
                    "text": {
                        "text": [get_text('hours_summary', language_code)]
                    }
                }
            ]
        }
        return jsonify(rich_response)
    except:
        # Fallback to English
        response_text = f"🍽️ {RESTAURANT_INFO['name']}\n{RESTAURANT_INFO['description']}\n📍 Address: {RESTAURANT_INFO['address']}"
        return jsonify({'fulfillmentText': response_text})


def handle_contact_human(language_code='en'):
    """Handle human contact request with multilingual support"""
    try:
        from translations import get_text
        
        # Provide multiple ways for customers to reach human staff
        rich_response = {
            # Simple fallback message
            "fulfillmentText": get_text('contact_staff', language_code),
            # Rich response with contact options
            "fulfillmentMessages": [
                {
                    # Header message
                    "text": {
                        "text": [get_text('contact_staff', language_code)]
                    }
                },
                {
                    # Phone contact option
                    "text": {
                        "text": [get_text('phone_label', language_code, phone=RESTAURANT_INFO['phone'])]
                    }
                },
                {
                    # Email contact option
                    "text": {
                        "text": [get_text('email_label', language_code, email=RESTAURANT_INFO['email'])]
                    }
                },
            ]
        }
        return jsonify(rich_response)
    except:
        # Fallback to English
        response_text = f"👨‍💼 Contact our staff:\n📞 Phone: {RESTAURANT_INFO['phone']}\n📧 Email: {RESTAURANT_INFO['email']}"
        return jsonify({'fulfillmentText': response_text})


def handle_restaurant_location(language_code='en'):
    """Handle restaurant location request with multilingual support"""
    try:
        from translations import get_text
        
        # Provide restaurant location information
        rich_response = {
            # Simple location fallback
            "fulfillmentText": get_text('location_header', language_code, restaurant=RESTAURANT_INFO['name']),
            # Rich response with detailed location
            "fulfillmentMessages": [
                {
                    # Location header
                    "text": {
                        "text": [get_text('location_header', language_code, restaurant=RESTAURANT_INFO['name'])]
                    }
                },
                {
                    # Full address
                    "text": {
                        "text": [get_text('location_address', language_code, address=RESTAURANT_INFO['address'])]
                    }
                },
            ]
        }
        return jsonify(rich_response)
    except:
        # Fallback to English
        response_text = f"📍 {RESTAURANT_INFO['name']} Location:\n🏠 Address: {RESTAURANT_INFO['address']}"
        return jsonify({'fulfillmentText': response_text})
