"""
Handlers for restaurant information management
"""
from flask import jsonify

# Import from our modules
from config import RESTAURANT_INFO, MENU


def handle_show_menu(parameters):
    """Handle menu display - MULTIPLE MESSAGES for better user experience"""
    # Extract menu category from user parameters (e.g., "breakfast", "lunch", "dinner")
    menu_category = parameters.get('menu-category', '').lower()
    
    # If user requested a specific menu category, show only that category
    if menu_category and menu_category in MENU:
        items = MENU[menu_category]
        # Format single category response with numbered items
        response_text = f"🍽️ {menu_category.title()} Menu:\n\n" + "\n".join([f"{i}. {item}" for i, item in enumerate(items, 1)])
        return jsonify({'fulfillmentText': response_text})
    else:
        # Show complete menu using multiple messages for better readability
        # This creates separate chat bubbles for each menu section
        rich_response = {
            # Main fulfillment text (fallback for platforms that don't support rich responses)
            "fulfillmentText": f"🍽️ {RESTAURANT_INFO['name']} Menu:",
            # Rich response with multiple message bubbles
            "fulfillmentMessages": [
                {
                    # Header message with restaurant name
                    "text": {
                        "text": [f"🍽️ {RESTAURANT_INFO['name']} Menu:"]
                    }
                },
                {
                    # Breakfast menu section with bullet points
                    "text": {
                        "text": [f"☀️ BREAKFAST:\n" + "\n".join([f"• {item}" for item in MENU['breakfast']])]
                    }
                },
                {
                    # Lunch menu section with bullet points
                    "text": {
                        "text": [f"🍛 LUNCH:\n" + "\n".join([f"• {item}" for item in MENU['lunch']])]
                    }
                },
                {
                    # Dinner menu section with bullet points
                    "text": {
                        "text": [f"🌅 DINNER:\n" + "\n".join([f"• {item}" for item in MENU['dinner']])]
                    }
                },
                {
                    # Beverages section with bullet points
                    "text": {
                        "text": [f"🥤 BEVERAGES:\n" + "\n".join([f"• {item}" for item in MENU['beverages']])]
                    }
                },
            ]
        }
        return jsonify(rich_response)


def handle_opening_hours():
    """Handle opening hours display - MULTIPLE MESSAGES for clear presentation"""
    # Create structured response with separate messages for different day schedules
    rich_response = {
        # Fallback text for simple platforms
        "fulfillmentText": f"🕐 {RESTAURANT_INFO['name']} Opening Hours:",
        # Rich messages for platforms supporting multiple bubbles
        "fulfillmentMessages": [
            {
                # Header message with restaurant name
                "text": {
                    "text": [f"🕐 {RESTAURANT_INFO['name']} Opening Hours:"]
                }
            },
            {
                # Weekday hours (Monday through Saturday)
                "text": {
                    "text": ["📅 Monday - Saturday:\n09:00 AM - 09:00 PM"]
                }
            },
            {
                # Sunday hours (different schedule for weekend)
                "text": {
                    "text": ["📅 Sunday:\n10:00 AM - 08:00 PM"]
                }
            },
        ]
    }
    return jsonify(rich_response)


def handle_restaurant_info():
    """Handle restaurant information display - MULTIPLE MESSAGES for comprehensive info"""
    # Create detailed restaurant information using multiple message bubbles
    # This breaks down information into digestible chunks for better user experience
    rich_response = {
        # Simple fallback text
        "fulfillmentText": f"🍽️ {RESTAURANT_INFO['name']}",
        # Detailed rich response with separate sections
        "fulfillmentMessages": [
            {
                # Restaurant name header
                "text": {
                    "text": [f"🍽️ {RESTAURANT_INFO['name']}"]
                }
            },
            {
                # Restaurant description/about section
                "text": {
                    "text": [f"{RESTAURANT_INFO['description']}"]
                }
            },
            {
                # Physical address information
                "text": {
                    "text": [f"📍 Address:\n{RESTAURANT_INFO['address']}"]
                }
            },
            {
                # Phone contact information
                "text": {
                    "text": [f"📞 Phone:\n{RESTAURANT_INFO['phone']}"]
                }
            },
            {
                # Email contact information
                "text": {
                    "text": [f"📧 Email:\n{RESTAURANT_INFO['email']}"]
                }
            },
            {
                # Quick summary of operating hours
                "text": {
                    "text": ["🕐 Hours:\nMon-Sat 9AM-9PM\nSun 10AM-8PM"]
                }
            }
        ]
    }
    return jsonify(rich_response)


def handle_contact_human():
    """Handle human contact request - MULTIPLE MESSAGES for clear contact options"""
    # Provide multiple ways for customers to reach human staff
    # Separated into different messages for clarity
    rich_response = {
        # Simple fallback message
        "fulfillmentText": "👨‍💼 Contact our staff:",
        # Rich response with contact options
        "fulfillmentMessages": [
            {
                # Header message indicating staff contact
                "text": {
                    "text": ["👨‍💼 Contact our staff:"]
                }
            },
            {
                # Phone contact option with number
                "text": {
                    "text": [f"📞 Call:\n{RESTAURANT_INFO['phone']}"]
                }
            },
            {
                # Email contact option with address
                "text": {
                    "text": [f"📧 Email:\n{RESTAURANT_INFO['email']}"]
                }
            },
        ]
    }
    return jsonify(rich_response)


def handle_restaurant_location():
    """Handle restaurant location request - MULTIPLE MESSAGES for location info"""
    # Provide restaurant location information in a clear, structured format
    rich_response = {
        # Simple location fallback
        "fulfillmentText": f"📍 {RESTAURANT_INFO['name']} Location:",
        # Rich response with detailed location
        "fulfillmentMessages": [
            {
                # Location header with restaurant name
                "text": {
                    "text": [f"📍 {RESTAURANT_INFO['name']} Location:"]
                }
            },
            {
                # Full address information with house icon
                "text": {
                    "text": [f"🏠 Address:\n{RESTAURANT_INFO['address']}"]
                }
            },
        ]
    }
    return jsonify(rich_response)
